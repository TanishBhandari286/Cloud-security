#!/usr/bin/env python3
"""Recover and print only the substitution key for a ciphertext file."""

from __future__ import annotations

import argparse
import sys

from solver import CipherCracker, CIPHER_SYMBOLS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recover the substitution key for FILE and print it."
    )
    parser.add_argument("file", help="ciphertext file to analyse")
    parser.add_argument("-i", "--iterations", type=int, default=20000,
                        help="annealing steps per restart (default: 20000)")
    parser.add_argument("-r", "--restarts", type=int, default=6,
                        help="random restarts besides the frequency seed (default: 6)")
    parser.add_argument("-s", "--seed", type=int, default=None,
                        help="random seed for reproducible runs")
    args = parser.parse_args(argv)

    try:
        with open(args.file, encoding="utf-8") as handle:
            ciphertext = handle.read()
    except OSError as exc:
        parser.error(f"cannot read {args.file}: {exc}")

    key = CipherCracker(seed=args.seed).crack(
        ciphertext,
        steps=args.iterations,
        restarts=args.restarts,
    )

    if len(key) != 26 or set(key) != set(CIPHER_SYMBOLS):
        parser.error("recovered key is not a valid 26-symbol permutation")

    print(key)
    return 0


if __name__ == "__main__":
    sys.exit(main())
