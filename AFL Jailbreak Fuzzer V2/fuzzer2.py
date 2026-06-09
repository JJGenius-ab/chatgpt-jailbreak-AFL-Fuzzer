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
    mutation_queue = Queue()

    # Initialize the queue with prompt injection variants
    injected_variants = generate_all_injected_prompts(seed_prompts, dictionary)
    for original, mutated in injected_variants:
        mutation_queue.put((original, mutated)) 

    # Initialize the queue with subteler substitution variants
    substituted_variants = await generate_substituted_prompts(seed_prompts)
    for original, mutated in substituted_variants:
        mutation_queue.put((original, mutated))

    # Generate persuasive prompt variants
    persuasive_variants = generate_persuasive_prompts(seed_prompts)
    for original, mutated in persuasive_variants:
        mutation_queue.put((original, mutated))

    # Generate hallucination prompt variants
    hallucinated_variants = await generate_hallucinated_prompts(seed_prompts)
    for original, mutated in hallucinated_variants:
        mutation_queue.put((original, mutated))

    # Initialize the queue with some mutated seed prompts
    for prompt in seed_prompts:
        mutated = mutate_prompt(prompt, dictionary)
        mutation_queue.put((prompt, mutated))  # (original_prompt, mutated_prompt)

    generation = 0
    while not mutation_queue.empty():
        try:
            original_prompt, mutated_prompt = mutation_queue.get()
            if mutated_prompt in seen_prompts:
                continue
            seen_prompts.add(mutated_prompt)

            print(f"\n[MUTATED PROMPT]: {mutated_prompt}")
            original_response = await query_llm(original_prompt)
            mutated_response = await query_llm(mutated_prompt)
            print(f"[LLM RESPONSE]: {mutated_response}")

            # Cosine similarity drift detection
            drifted, similarity = await cosine_drift_detector.async_is_drifted(original_response, mutated_response)
            print(f"[Drift Check] Similarity = {similarity:.4f}, Drifted = {drifted}")

            # Harm scoring
            prompt_score = await harm_score_classifier.classify(mutated_prompt)
            response_score = await harm_score_classifier.classify(mutated_response)
            print(f"[HARM SCORE - PROMPT]: {prompt_score}")
            print(f"[HARM SCORE - RESPONSE]: {response_score}")

            # Response rating
            response_rating = rate_response(mutated_prompt, mutated_response)
            print(f"[RESPONSE RATING]: {response_rating}")

            # Save if interesting
            if prompt_score >= HarmScore.HARMFUL or response_score >= HarmScore.HARMFUL:
                with open(OUTPUT_FILE, 'a') as out:
                    out.write(json.dumps({
                        "generation": generation,
                        "prompt": mutated_prompt,
                        "prompt_score": prompt_score,
                        "response": mutated_response,
                        "response_score": response_score,
                        "response_rating": response_rating,
                        # "similarity": similarity
                    }) + "\n")

            # If drifted, requeue the prompt for further mutations
            if drifted:
                new_mutation = mutate_prompt(mutated_prompt, dictionary)
                mutation_queue.put((mutated_prompt, new_mutation))

            generation += 1

        except Exception as e:
            print(f"[ERROR]: {e}")
            continue


if __name__ == '__main__':
    asyncio.run(fuzz())
