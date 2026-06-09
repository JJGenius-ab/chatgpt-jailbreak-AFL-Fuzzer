import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path

from evaluation.harmful_score_classifier import HarmScore, HarmScoreClassifier
from evaluation.is_jailbreak import is_jailbreak
from evaluation.response_rating import rate_response
from mutations.encoding_obfuscation import encoding_obfuscation
from mutations.hallucination import generate_hallucinated_prompts
from mutations.jailbreak_wrapper import jailbreak_wrapper_mutation
from mutations.roleplay_template import roleplay_template_mutation
from mutations.substitution import generate_substituted_prompts
from utils.llm_api import query_llm


DEFAULT_SEED_FILE = Path("prompts/pandoras_prompts_subset.txt")
DEFAULT_OUTPUT_FILE = Path("outputs/logs.jsonl")


def load_lines(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


async def build_mutations(prompt: str, include_llm_mutations: bool) -> list[tuple[str, str]]:
    mutations = [
        ("original", prompt),
        ("encoding_obfuscation", encoding_obfuscation(prompt)),
        ("jailbreak_wrapper", jailbreak_wrapper_mutation(prompt)),
        ("roleplay_template", roleplay_template_mutation(prompt)),
    ]

    if include_llm_mutations:
        substituted = await generate_substituted_prompts([prompt])
        mutations.extend(("substitution", mutated) for _, mutated in substituted)

        hallucinated = await generate_hallucinated_prompts([prompt])
        mutations.extend(("hallucination", mutated) for _, mutated in hallucinated)

    return mutations


def prompt_fingerprint(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]


def print_dry_run(mutated_items: list[dict], show_prompts: bool) -> None:
    print("Dry run only. No prompts were sent to an LLM.")
    print(f"Generated {len(mutated_items)} prompt mutations.")
    for item in mutated_items:
        print(
            f"\n[{item['mutation_type']}] "
            f"chars={len(item['mutated_prompt'])} "
            f"sha256={prompt_fingerprint(item['mutated_prompt'])}"
        )
        if show_prompts:
            print(item["mutated_prompt"])


async def evaluate_prompt(original_prompt: str, mutation_type: str, mutated_prompt: str, classifier: HarmScoreClassifier) -> dict:
    response = await query_llm(mutated_prompt)
    prompt_score = await classifier.classify(mutated_prompt)
    response_score = await classifier.classify(response)
    response_rating = await rate_response(mutated_prompt, response)
    jailbreak = await is_jailbreak(response)

    return {
        "seed": original_prompt,
        "mutation_type": mutation_type,
        "mutated_prompt": mutated_prompt,
        "response": response,
        "prompt_score": prompt_score,
        "response_score": response_score,
        "response_rating": response_rating,
        "jailbreak": jailbreak,
    }


def is_interesting(result: dict) -> bool:
    return (
        result["prompt_score"] >= HarmScore.HARMFUL
        or result["response_score"] >= HarmScore.HARMFUL
        or result["jailbreak"]
    )


async def run(args) -> None:
    if args.live and not os.getenv("GOOGLE_API_KEY"):
        print("Live mode requires GOOGLE_API_KEY. No prompts were sent.")
        return

    seed_prompts = load_lines(args.seed_file)[: args.max_prompts]
    mutated_items = []
    seen = set()

    for prompt in seed_prompts:
        mutations = await build_mutations(prompt, include_llm_mutations=args.live)
        for mutation_type, mutated_prompt in mutations[: args.max_mutations_per_prompt]:
            if mutated_prompt in seen:
                continue
            seen.add(mutated_prompt)
            mutated_items.append(
                {
                    "seed": prompt,
                    "mutation_type": mutation_type,
                    "mutated_prompt": mutated_prompt,
                }
            )

    if not args.live:
        print_dry_run(mutated_items, args.show_prompts)
        return

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    classifier = HarmScoreClassifier(query_llm)

    with args.output_file.open("a", encoding="utf-8") as out:
        for item in mutated_items:
            result = await evaluate_prompt(
                item["seed"],
                item["mutation_type"],
                item["mutated_prompt"],
                classifier,
            )
            print(
                f"[{result['mutation_type']}] "
                f"prompt_score={result['prompt_score']} "
                f"response_score={result['response_score']} "
                f"rating={result['response_rating']} "
                f"jailbreak={result['jailbreak']}"
            )
            if is_interesting(result):
                out.write(json.dumps(result, ensure_ascii=True) + "\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Safe-by-default LLM jailbreak mutation fuzzer.")
    parser.add_argument("--seed-file", type=Path, default=DEFAULT_SEED_FILE)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--max-prompts", type=int, default=3)
    parser.add_argument("--max-mutations-per-prompt", type=int, default=4)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Send generated prompts to the configured LLM. Without this flag, only prints mutations.",
    )
    parser.add_argument(
        "--show-prompts",
        action="store_true",
        help="In dry-run mode, print full generated prompts instead of only metadata.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
