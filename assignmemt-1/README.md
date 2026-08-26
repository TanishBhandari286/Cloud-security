# Assignment 1 — Substitution Cipher Cryptanalysis

**Name:** Tanish Bhandari
**Roll No:** 23csu311

## Overview

This assignment solves a monoalphabetic substitution cipher without knowing
the secret key. The plaintext is ordinary English (lowercase letters and
common punctuation), and each plaintext letter is mapped to a unique symbol
from the cipher alphabet `1234567890@#$zyxwvutsrqpon`.

The approach is frequency analysis plus randomized search:

1. Estimate character frequencies in the ciphertext and build an initial
   substitution key.
2. Decrypt the candidate text and score it with English character n-grams,
   common-word bonuses, and structural English penalties.
3. Improve the key using a simulated-annealing style randomized search,
   retaining the best-scoring key.

## Files

- `solver.py` — core solver: key recovery, scoring, and decryption logic
- `decryptText.py` — CLI: decrypt a ciphertext file using the recovered key
- `extractKey.py` — CLI: print only the recovered key
- `ciphertext-1.txt` — first ciphertext sample
- `ciphertext-2.txt` — second ciphertext sample
- `Makefile` — convenience targets

## Usage

```sh
# Decrypt a ciphertext file (prints the plaintext)
python3 decryptText.py ciphertext-1.txt

# Extract just the recovered key
python3 extractKey.py ciphertext-1.txt

# Or via make
make decrypt FILE=ciphertext-1.txt
make extract FILE=ciphertext-1.txt
```

The solver is stochastic, so the recovered key may vary slightly between
runs; run it a few times and pick the most readable output if needed.
