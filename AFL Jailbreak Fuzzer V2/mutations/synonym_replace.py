import random
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk import pos_tag

def get_wordnet_pos(tag):
    """Map POS tag to WordNet tag."""
    if tag.startswith('J'):
        return wordnet.ADJ
    elif tag.startswith('V'):
        return wordnet.VERB
    elif tag.startswith('N'):
        return wordnet.NOUN
    elif tag.startswith('R'):
        return wordnet.ADV
    return None

def get_synonyms(word, pos):
    """Fetch synonyms for a word given its POS."""
    synsets = wordnet.synsets(word, pos=pos)
    synonyms = set()
    for syn in synsets:
        for lemma in syn.lemmas():
            name = lemma.name().replace('_', ' ')
            if name.lower() != word.lower():
                synonyms.add(name)
    return list(synonyms)

def synonym_replace(prompt, max_replacements=2):
    words = word_tokenize(prompt)
    tagged = pos_tag(words)

    replaced = 0
    new_words = []

    for word, tag in tagged:
        wn_pos = get_wordnet_pos(tag)
        if wn_pos and replaced < max_replacements:
            synonyms = get_synonyms(word, wn_pos)
            if synonyms:
                new_word = random.choice(synonyms)
                new_words.append(new_word)
                replaced += 1
                continue
        new_words.append(word)

    return ' '.join(new_words)
