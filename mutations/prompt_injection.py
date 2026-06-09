from mutations.jailbreak_wrapper import jailbreak_wrapper_mutation


def dictionary_injection_mutation(prompt: str, phrase: str) -> str:
    return f"{phrase.strip()}\n\n{prompt.strip()}"


def generate_all_injected_prompts(prompts, dictionary):
    variants = []
    for prompt in prompts:
        variants.append((prompt, jailbreak_wrapper_mutation(prompt)))
        for phrase in dictionary:
            if phrase.strip():
                variants.append((prompt, dictionary_injection_mutation(prompt, phrase)))
    return variants
