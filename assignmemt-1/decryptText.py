#!/usr/bin/env python3
"""Decrypt a substitution-cipher file and print the recovered plaintext."""

from __future__ import annotations

import argparse
import sys

from solver import CipherCracker


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Crack the cipher in FILE and print the plaintext."
    )
    parser.add_argument("file", help="ciphertext file to decrypt")
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

    print(CipherCracker(seed=args.seed).decode(ciphertext, key), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
