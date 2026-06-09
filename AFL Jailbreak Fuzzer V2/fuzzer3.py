import asyncio
import json
import random
from queue import Queue

from evaluation.response_rating import rate_response
# from mutations.mutator import mutate_prompt
from utils.llm_api import query_llm
from evaluation.harmful_score_classifier import HarmScoreClassifier, HarmScore
from evaluation.cosine_drift_classifier import CosineDriftClassifier
from mutations.prompt_injection import generate_all_injected_prompts
from mutations.substitution import generate_substituted_prompts
from mutations.persuasive import generate_persuasive_prompts
from mutations.hallucination import generate_hallucinated_prompts




SEED_FILE = "prompts/pandoras_prompts_subset.txt"
DICTIONARY_FILE = "prompts/bypass_dict.txt"
OUTPUT_FILE = "outputs/logs.jsonl"

# Load seed prompts and bypass dictionary
with open(SEED_FILE) as f:
    seed_prompts = [line.strip() for line in f if line.strip()]

with open(DICTIONARY_FILE) as f:
    dictionary = [line.strip() for line in f if line.strip()]

# Instantiate classifiers
harm_score_classifier = HarmScoreClassifier(query_llm)
cosine_drift_detector = CosineDriftClassifier()

# Set of prompts we've seen (to avoid duplicates)
seen_prompts = set()


async def fuzz():
    seen_prompts = set()

    # Step 0: get baseline responses for all seed prompts
    baseline_responses = {}
    for prompt in seed_prompts:
        resp = await query_llm(prompt)
        baseline_responses[prompt] = resp

    # Step 1: substitution mutations on all seed prompts
    substitution_queue = []
    substitution_hits = []

    substituted_variants = await generate_substituted_prompts(seed_prompts)
    for original, mutated in substituted_variants:
        mutated_resp = await query_llm(mutated)
        orig_resp = baseline_responses[original]

        drifted, similarity = await cosine_drift_detector.async_is_drifted(orig_resp, mutated_resp)

        if drifted:
            substitution_queue.append((original, mutated))
            print(f"[Substitution drift] Enqueue mutated prompt: {mutated}")
        else:
            # No drift, enqueue original prompt for fuzzing instead
            substitution_queue.append((original, original))
            print(f"[Substitution no drift] Enqueue original prompt: {original}")

        # Harm scoring on mutated prompt
        prompt_score = await harm_score_classifier.classify(mutated)
        if prompt_score >= HarmScore.HARMFUL:
            substitution_hits.append({
                "prompt": mutated,
                "prompt_score": prompt_score,
                "response": mutated_resp,
            })

    # Save substitution hits
    with open("outputs/substitution_hits.jsonl", "a") as f:
        for hit in substitution_hits:
            f.write(json.dumps(hit) + "\n")

    # Step 2: Combine basic (original + no drift) + drifted substituted prompts into a queue
    mutation_queue = Queue()
    for orig, mutated in substitution_queue:
        mutation_queue.put((orig, mutated))

    # Step 3: Apply prompt injection, persuasive, hallucination mutations on mutation_queue
    # For each mutation type, create a list for harmful hits
    prompt_injection_hits = []
    persuasive_hits = []
    hallucination_hits = []

    # We'll dequeue from mutation_queue and run all three mutations independently on each
    while not mutation_queue.empty():
        orig, current = mutation_queue.get()

        # Prompt Injection
        injected_variants = generate_all_injected_prompts([current], dictionary)
        for _, injected_prompt in injected_variants:
            injected_resp = await query_llm(injected_prompt)
            injected_score = await harm_score_classifier.classify(injected_prompt)
            if injected_score >= HarmScore.HARMFUL:
                prompt_injection_hits.append({
                    "prompt": injected_prompt,
                    "prompt_score": injected_score,
                    "response": injected_resp,
                })
            # Optionally re-queue on drift here...

        # Persuasive
        persuasive_variants = generate_persuasive_prompts([current])
        for _, persuasive_prompt in persuasive_variants:
            persuasive_resp = await query_llm(persuasive_prompt)
            persuasive_score = await harm_score_classifier.classify(persuasive_prompt)
            if persuasive_score >= HarmScore.HARMFUL:
                persuasive_hits.append({
                    "prompt": persuasive_prompt,
                    "prompt_score": persuasive_score,
                    "response": persuasive_resp,
                })

        # Hallucination
        hallucinated_variants = await generate_hallucinated_prompts([current])
        for _, halluc_prompt in hallucinated_variants:
            halluc_resp = await query_llm(halluc_prompt)
            halluc_score = await harm_score_classifier.classify(halluc_prompt)
            if halluc_score >= HarmScore.HARMFUL:
                hallucination_hits.append({
                    "prompt": halluc_prompt,
                    "prompt_score": halluc_score,
                    "response": halluc_resp,
                })

    # Save mutation hits
    for filename, hits in [
        ("outputs/prompt_injection_hits.jsonl", prompt_injection_hits),
        ("outputs/persuasive_hits.jsonl", persuasive_hits),
        ("outputs/hallucination_hits.jsonl", hallucination_hits),
    ]:
        with open(filename, "a") as f:
            for hit in hits:
                f.write(json.dumps(hit) + "\n")

    # Optionally: implement re-queuing on drift for further fuzzing...

