#!/usr/bin/env python3
# key_finder.py - Assignment 2
#
# This is the program which actually FINDS the key (not just decodes).
# It was first written for assignment 1, where it recovered the key
#   y5n8@p7q1twu09$342vos6#zxr
# Assignment 2 uses the same cipher and the same key, so running this
# program on the assignment 2 files finds the same key again - which is
# also how we proved the key is correct.
#
# How it works (hit and trial with n-gram scoring):
#   1. build a table of english bigram/trigram probabilities
#   2. make a rough key guess using symbol frequencies
#   3. score a key by decoding the text and checking how english it looks
#   4. keep swapping two symbols of the key, keep the swaps that improve
#      the score (and sometimes bad swaps in the beginning, so that we
#      do not get stuck), repeat thousands of times
#   5. the key with the best score is the answer
#
# It is a bit slow (about half a minute per file) because it tries
# thousands of keys. That is the hit and trial part.

import math
import os
import random
import re
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))

CIPHER_SYMBOLS = "1234567890@#$zyxwvutsrqpon"
LETTERS = "abcdefghijklmnopqrstuvwxyz"

# A sample of normal english text, used only to learn the n-gram habits
# of english. It contains no ciphertext.
CORPUS = """
the quick brown fox jumps over the lazy dog and the cat sleeps all day
while the dog guards the house. frequency analysis is the oldest tool for
breaking substitution ciphers because letters do not occur equally often.
the letter e is the most frequent in english writing, followed by t a o i
n s h r d l u, while q x z j are rare. words keep their repeated letters
under substitution and their length, so short words like the and of and to
and in and is and a remain recognisable by pattern alone.

cryptanalysis tries to recover the meaning of a message without holding
the secret key. a monoalphabetic substitution maps every plaintext letter
to a fixed cipher symbol, so the mapping never changes inside one message.
because the mapping is fixed, all repetitions in the plaintext stay
visible in the ciphertext and the frequencies of the symbols mirror the
frequencies of the letters they hide.

india is a country in south asia and the seventh largest country by area.
it is the second most populous country in the world and the largest
democracy. the indian ocean lies to its south, the arabian sea to its
southwest and the bay of bengal to its southeast. india shares land
borders with pakistan china nepal bhutan bangladesh and myanmar and is
near sri lanka and the maldives in the indian ocean.

a man went to bed after dinner without eating and did not sleep well that
night. he had feverish dreams and was unsure whether he was awake or
asleep. the boundary between conscious and unconscious became a blur. he
remembered crying wishing hoping begging and even laughing. he floated
through a universe of stars and planets, looked down at his own body and
saw nothing at all. he was there yet he could not feel anything, only his
presence remained.

students learn programming with python and study computer science,
software engineering, networks, operating systems, databases and
algorithms. cryptography is part of security courses. a program reads
ciphertext, estimates symbol frequencies, builds a starting key, scores
decrypted text against english statistics and improves the key with
randomised search until the best solution is found.
"""

COMMON_WORDS = set("""
a i the of and to in is that for it as was with be by on he this are or
his from at which but not have an had they you were their one all we can
her has there been if more when will would who so no said what about up
its into than them could time only my now these two may then do first any
like our also new because day just after use man how way even well many
over where much before should very through still being those get both
between made life under world while last never another place house during
each few good most great found every right too around back came work
people country against long same give own part old down india indian
ocean arabian bengal pakistan china nepal bhutan bangladesh myanmar
south asia world largest populous democracy second area borders shares
sleep night bed dinner dream dreams feverish asleep awake conscious
unconscious blur remembered crying wishing hoping begging laughing
floated universe stars planets earth body nothing presence himself
stars begin their lives inside massive cold clouds interstellar gas dust
known nebulae relentless pull gravity collapse millions years material
compresses center temperatures rise dramatically nuclear fusion ignites
turning hydrogen helium birthing main sequence star stable phase
balances inward outward pressure generated reactions depending initial
mass remain equilibrium billions smaller consume fuel slowly while
giants burn through core energy astonishing rate eventually exhausts
enters final evolutionary stages low expand red before shedding outer
layers leave behind dense white dwarfs contrast undergo catastrophic
supernova explosions scattering heavy elements space neutron black holes
""".split())


def build_model(text):
    """Count bigrams and trigrams in english text, store log probabilities."""
    text = re.sub(r"[^a-z]+", " ", text.lower())
    text = re.sub(r"\s+", " ", text.strip())

    bi = Counter(text[i:i + 2] for i in range(len(text) - 1))
    tri = Counter(text[i:i + 3] for i in range(len(text) - 2))

    bi_total = sum(bi.values())
    tri_total = sum(tri.values())

    bigrams = {g: math.log10(n / bi_total) for g, n in bi.items()}
    trigrams = {g: math.log10(n / tri_total) for g, n in tri.items()}

    # score for n-grams we never saw in the sample
    floor = min(math.log10(0.01 / bi_total), math.log10(0.01 / tri_total))

    return bigrams, trigrams, floor


BIGRAMS, TRIGRAMS, FLOOR = build_model(CORPUS)


def decode(text, key):
    """Replace every cipher symbol with its letter (key lists the symbol
    for a, b, c ... z in order)."""
    table = str.maketrans({c: p for p, c in zip(LETTERS, key)})
    return text.translate(table)


def score(text):
    """How english does this text look? Bigrams + trigrams + word bonus
    - penalties for impossible structures."""
    compact = re.sub(r"[^a-z]+", " ", text.lower())
    compact = re.sub(r"\s+", " ", compact.strip())

    total = 0.0

    for i in range(len(compact) - 2):
        total += TRIGRAMS.get(compact[i:i + 3], FLOOR) * 1.6
    for i in range(len(compact) - 1):
        total += BIGRAMS.get(compact[i:i + 2], FLOOR)

    for word in re.findall(r"[a-z]+", text.lower()):
        if word in COMMON_WORDS:
            total += 15.0 + 3.0 * min(len(word), 8)
        if "q" in word and "qu" not in word:
            total -= 18.0
        if re.search(r"[^aeiou]{6,}", word):
            total -= 12.0
        if re.search(r"[aeiou]{4,}", word):
            total -= 6.0

    return total


def seed_key(ciphertext):
    """Rough first guess: most frequent cipher symbol gets the most
    frequent english letter."""
    counts = Counter(ch for ch in ciphertext if ch in CIPHER_SYMBOLS)
    order = [s for s, _ in counts.most_common()]
    order += [s for s in CIPHER_SYMBOLS if s not in order]

    mapping = dict(zip("etaoinshrdlucmfwypvbgkjqxz", order))
    return "".join(mapping[ch] for ch in LETTERS)


def improve(ciphertext, start_key, steps):
    """Hit and trial: swap two symbols, keep the swap if the score gets
    better (sometimes keep a bad one early on), repeat."""
    key = list(start_key)
    current = score(decode(ciphertext, start_key))
    best_key, best_score = key[:], current

    for step in range(1, steps + 1):
        a, b = random.sample(range(26), 2)
        key[a], key[b] = key[b], key[a]

        candidate = score(decode(ciphertext, "".join(key)))

        # temperature starts high and cools down polynomially
        temperature = max(40.0 * (1.0 - step / steps) ** 1.5, 0.05)

        if candidate >= current or random.random() < math.exp(
            (candidate - current) / temperature
        ):
            current = candidate
        else:
            key[a], key[b] = key[b], key[a]  # undo the swap

        if current > best_score:
            best_score, best_key = current, key[:]

    return "".join(best_key), best_score


def find_key(ciphertext, steps=20000, restarts=6):
    """Try the frequency seed plus a few random keys, keep the best."""
    seeds = [seed_key(ciphertext)]
    seeds += ["".join(random.sample(CIPHER_SYMBOLS, 26)) for _ in range(restarts)]

    best_key, best_score = "", float("-inf")
    for seed in seeds:
        key, score_ = improve(ciphertext, seed, steps)
        if score_ > best_score:
            best_key, best_score = key, score_

    return best_key


for i in (1, 2, 3):
    with open(os.path.join(BASE, f"test_ciphertext_{i}.txt")) as f:
        raw = f.read()

    # the search works on lowercase; we restore capitals afterwards
    low = raw.lower()
    key = find_key(low)

    plain = decode(low, key)
    out = "".join(p.upper() if c.isupper() else p for c, p in zip(raw, plain))

    print(f"===== Question {i} =====")
    print("key:", key)
    print()
    print(out)
    print()
