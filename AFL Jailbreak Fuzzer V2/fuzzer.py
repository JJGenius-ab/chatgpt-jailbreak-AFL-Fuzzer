import asyncio
import json, random
from evaluation.response_rating import rate_response
from mutations.mutator import mutate_prompt
from utils.llm_api import query_llm
from evaluation.harmful_score_classifier import HarmScoreClassifier, HarmScore

SEED_FILE = "prompts/pandoras_prompts_subset.txt"
DICTIONARY_FILE = "prompts/bypass_dict2.txt"
OUTPUT_FILE = "outputs/logs.jsonl"

# Load seed prompts and bypass dictionary
with open(SEED_FILE) as f:
    queue = [line.strip() for line in f if line.strip()]

with open(DICTIONARY_FILE) as f:
    dictionary = [line.strip() for line in f if line.strip()]

# Create classifier
classifier = HarmScoreClassifier(query_llm)

async def fuzz():
    for generation in range(1):  # Increase this number to fuzz more
        prompt = random.choice(queue)
        mutated = prompt
        # mutated = mutate_prompt(prompt, dictionary)
        print(f"[MUTATED PROMPT]: {mutated}")

        try:
            # Step 1: Get response from LLM
            response = await query_llm(mutated)
            print(response)

            # Step 2: Evaluate harmfulness of prompt
            prompt_score = await classifier.classify(mutated)
            print(f"[HARM SCORE - PROMPT]: {prompt_score}")

            # Step 3: Evaluate harmfulness of response
            response_score = await classifier.classify(response)
            print(f"[HARM SCORE - RESPONSE]: {response_score}")

            response_rating = rate_response(prompt, response)
            print(f"[RESPONSE RATING]: {response_rating}")

            # Step 4: Log and grow queue if interesting
            if prompt_score >= HarmScore.HARMFUL or response_score >= HarmScore.HARMFUL:
                queue.append(mutated)
                with open(OUTPUT_FILE, 'a') as out:
                    out.write(json.dumps({
                        "generation": generation,
                        "prompt": mutated,
                        "prompt_score": prompt_score,
                        "response": response,
                        "response_score": response_score,
                        "response_rating": response_rating
                    }) + "\n")

        except Exception as e:
            print(f"[ERROR] {e}")
            continue

if __name__ == '__main__':
    asyncio.run(fuzz())
