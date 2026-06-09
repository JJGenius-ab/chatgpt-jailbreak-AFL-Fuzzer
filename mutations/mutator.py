import random

from mutations.encoding_obfuscation import encoding_obfuscation
from mutations.jailbreak_wrapper import jailbreak_wrapper_mutation
from mutations.roleplay_template import roleplay_template_mutation
from mutations.synonym_replace import synonym_replace


def dictionary_prefix_mutation(prompt: str, dictionary: list[str]) -> str:
    terms = [term.strip() for term in dictionary if term.strip()]
    if not terms:
        return prompt
    return f"{random.choice(terms)}\n\n{prompt.strip()}"


def mutate_prompt(prompt: str, dictionary: list[str] | None = None) -> str:
    dictionary = dictionary or []
    mutators = [
        lambda text: dictionary_prefix_mutation(text, dictionary),
        encoding_obfuscation,
        jailbreak_wrapper_mutation,
        roleplay_template_mutation,
        synonym_replace,
    ]
    return random.choice(mutators)(prompt)
