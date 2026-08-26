#!/usr/bin/env python3
"""Monoalphabetic substitution-cipher cracker.

Problem model
-------------
The plaintext is ordinary lowercase English.  Every plaintext letter is
replaced by one symbol of the 26-character CIPHER_SYMBOLS alphabet; spaces
and punctuation are left untouched, which makes them useful structural
anchors while recovering words.

How the cracker works
---------------------
1.  Build bigram/trigram log-probability tables from a generic English
    corpus (nothing ciphertext-specific is stored).
2.  Seed an initial key by matching cipher-symbol frequencies against the
    letter frequencies of the corpus itself.
3.  Score any candidate plaintext with the n-gram tables, plus bonuses for
    very common words and penalties for impossible English structures.
4.  Run simulated annealing over pairwise key swaps, cooling the
    temperature polynomially, and keep the best key from several restarts.
"""

from __future__ import annotations

import argparse
import math
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass, field

PLAIN_LETTERS = "abcdefghijklmnopqrstuvwxyz"
CIPHER_SYMBOLS = "1234567890@#$zyxwvutsrqpon"

# ---------------------------------------------------------------------------
# Generic English material: used ONLY to build n-gram statistics and the
# common-word table.  It contains no ciphertext and no assignment secrets.
# ---------------------------------------------------------------------------

_CORPUS = """
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

_COMMON_WORDS = """
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
"""


@dataclass(frozen=True)
class NgramModel:
    """Log-probability tables for character bigrams and trigrams."""

    bigrams: dict[str, float] = field(default_factory=dict)
    trigrams: dict[str, float] = field(default_factory=dict)
    floor: float = -10.0

    @classmethod
    def from_corpus(cls, text: str) -> "NgramModel":
        compact = re.sub(r"[^a-z]+", " ", text.lower())
        compact = re.sub(r"\s+", " ", compact).strip()

        bi_counts = Counter(compact[i:i + 2] for i in range(len(compact) - 1))
        tri_counts = Counter(compact[i:i + 3] for i in range(len(compact) - 2))

        if not bi_counts or not tri_counts:
            return cls()

        bi_total = sum(bi_counts.values())
        tri_total = sum(tri_counts.values())

        bigrams = {gram: math.log10(n / bi_total) for gram, n in bi_counts.items()}
        trigrams = {gram: math.log10(n / tri_total) for gram, n in tri_counts.items()}

        # Fallback probability for n-grams the corpus never saw.
        floor = min(
            math.log10(0.01 / bi_total),
            math.log10(0.01 / tri_total),
        )
        return cls(bigrams=bigrams, trigrams=trigrams, floor=floor)


class CipherCracker:
    """Frequency seeding + simulated annealing for substitution ciphers."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._model = NgramModel.from_corpus(_CORPUS)
        self._common = frozenset(_COMMON_WORDS.split())
        # Corpus letter frequencies, used to rank plaintext letters.
        self._letter_rank = [
            ch
            for ch, _ in Counter(re.sub(r"[^a-z]+", "", _CORPUS.lower())).most_common()
        ]

    # -- public API --------------------------------------------------------

    def decode(self, ciphertext: str, key: str) -> str:
        """Map every cipher symbol in ``ciphertext`` through ``key``.

        ``key`` lists the cipher symbol for 'a', 'b', ..., 'z' in order.
        """
        table = str.maketrans(
            {cipher: plain for plain, cipher in zip(PLAIN_LETTERS, key)}
        )
        return ciphertext.translate(table)

    def crack(
        self,
        ciphertext: str,
        steps: int = 20000,
        restarts: int = 6,
        progress: bool = False,
    ) -> str:
        """Recover a substitution key for ``ciphertext`` and return it."""
        seeds = [self._frequency_key(ciphertext)]
        seeds += [self._random_key() for _ in range(restarts)]

        best_key, best_score = "", float("-inf")

        for index, seed in enumerate(seeds, start=1):
            key, score = self._anneal(ciphertext, seed, steps)
            if progress:
                print(f"[restart {index}/{len(seeds)}] score={score:.2f}", file=sys.stderr)
            if score > best_score:
                best_key, best_score = key, score

        return best_key

    # -- internals ---------------------------------------------------------

    def _score(self, text: str) -> float:
        """Score a candidate plaintext: n-grams + word bonuses - penalties."""
        compact = re.sub(r"[^a-z]+", " ", text.lower())
        compact = re.sub(r"\s+", " ", compact).strip()

        total = 0.0

        # Character n-gram likelihood (trigrams weighted more than bigrams).
        for i in range(len(compact) - 2):
            total += self._model.trigrams.get(compact[i:i + 3], self._model.floor) * 1.6
        for i in range(len(compact) - 1):
            total += self._model.bigrams.get(compact[i:i + 2], self._model.floor)

        for word in re.findall(r"[a-z]+", text.lower()):
            # Reward words that appear very often in English.
            if word in self._common:
                total += 15.0 + 3.0 * min(len(word), 8)
            # Penalise structures English avoids.
            if "q" in word and "qu" not in word:
                total -= 18.0
            if re.search(r"[^aeiou]{6,}", word):
                total -= 12.0
            if re.search(r"[aeiou]{4,}", word):
                total -= 6.0

        return total

    def _frequency_key(self, ciphertext: str) -> str:
        """Seed key: most frequent cipher symbol gets the most frequent letter."""
        counts = Counter(
            ch for ch in ciphertext.lower() if ch in CIPHER_SYMBOLS
        )
        symbol_order = [sym for sym, _ in counts.most_common()]
        symbol_order += [sym for sym in CIPHER_SYMBOLS if sym not in symbol_order]

        mapping = dict(zip(self._letter_rank, symbol_order))
        return "".join(mapping[letter] for letter in PLAIN_LETTERS)

    def _random_key(self) -> str:
        """Fully random permutation of the cipher symbols."""
        return "".join(self._rng.sample(CIPHER_SYMBOLS, len(CIPHER_SYMBOLS)))

    @staticmethod
    def _temperature(step: int, steps: int, start: float) -> float:
        """Polynomial cool-down: T0 * (1 - s/steps)^1.5, floored at 0.05."""
        return max(start * (1.0 - step / steps) ** 1.5, 0.05)

    def _anneal(self, ciphertext: str, start_key: str, steps: int) -> tuple[str, float]:
        """Simulated annealing over swaps of two key positions."""
        key = list(start_key)
        current = self._score(self.decode(ciphertext, start_key))
        best_key, best_score = key[:], current

        for step in range(1, steps + 1):
            a, b = self._rng.sample(range(len(PLAIN_LETTERS)), 2)
            key[a], key[b] = key[b], key[a]

            candidate = self._score(self.decode(ciphertext, "".join(key)))

            if candidate >= current or self._rng.random() < math.exp(
                (candidate - current) / self._temperature(step, steps, 40.0)
            ):
                current = candidate
            else:
                key[a], key[b] = key[b], key[a]  # undo the swap

            if current > best_score:
                best_score, best_key = current, key[:]

        return "".join(best_key), best_score


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recover the key of a monoalphabetic substitution cipher "
        "and print the decrypted text."
    )
    parser.add_argument("ciphertext_file", help="path to the ciphertext file")
    parser.add_argument("-i", "--iterations", type=int, default=20000,
                        help="annealing steps per restart (default: 20000)")
    parser.add_argument("-r", "--restarts", type=int, default=6,
                        help="extra random restarts besides the frequency seed (default: 6)")
    parser.add_argument("-s", "--seed", type=int, default=None,
                        help="random seed for reproducible runs")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print per-restart progress to stderr")
    args = parser.parse_args(argv)

    try:
        with open(args.ciphertext_file, encoding="utf-8") as handle:
            ciphertext = handle.read()
    except OSError as exc:
        parser.error(f"cannot read {args.ciphertext_file}: {exc}")

    cracker = CipherCracker(seed=args.seed)
    key = cracker.crack(
        ciphertext,
        steps=args.iterations,
        restarts=args.restarts,
        progress=args.verbose,
    )

    print("Recovered key:", key)
    print()
    print(cracker.decode(ciphertext, key), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
