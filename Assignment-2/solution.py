#!/usr/bin/env python3
# solution.py - Assignment 2
# Decode all three ciphertext files using the key from Assignment 1.

import os

# Folder where this script is, so the code runs from anywhere
# (VS Code sometimes runs from a different folder)
BASE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------
# How we found this key (in Assignment 1):
#
# The cipher is a monoalphabetic substitution cipher, meaning every
# plaintext letter is replaced by one fixed symbol. The cipher alphabet
# is "1234567890@#$zyxwvutsrqpon" (26 symbols for 26 letters) and the
# spaces are not encrypted, so we could see the word lengths.
#
# The clues we used:
#   1. "oq@" appeared 19 times as a 3-letter word -> the most common
#      3-letter english word is "the", so o=t, q=h, @=e.
#   2. "y98" appeared 8 times -> "and", so y=a, 9=n, 8=d.
#   3. "y" alone between spaces -> "a" or "i" (only 1-letter words).
#   4. "1981y" has the same symbol at position 1 and 4, and it was the
#      first word of the file -> "india" (i at position 1 and 4),
#      so 1=i and the passage was clearly about india.
#   5. Every new word confirmed the earlier guesses, like a crossword,
#      until all 26 symbols had a letter.
#
# We also wrote a program that automates this: it counts the symbol
# frequencies, scores how english-like the decoded text looks and keeps
# improving the key by swapping two symbols again and again (simulated
# annealing), then keeps the best key.
#
# The final key we recovered was:
#   KEY = "y5n8@p7q1twu09$342vos6#zxr"
# which means the cipher symbol for a is y, for b is 5, for c is n ...
# and for z is r.
#
# Assignment 2 uses the SAME cipher and the SAME key, so we just reused
# it here.
# ---------------------------------------------------------------------

KEY = "y5n8@p7q1twu09$342vos6#zxr"   # cipher symbol for a, b, c ... z
LETTERS = "abcdefghijklmnopqrstuvwxyz"  # english alphabet, used to pair with KEY

# Reverse mapping: cipher symbol -> plain letter
reverse = {}
for letter, symbol in zip(LETTERS, KEY):
    reverse[symbol] = letter


def decrypt(text):
    result = ""
    for ch in text:
        if ch.lower() in reverse:
            if ch.isupper():
                result += reverse[ch.lower()].upper()
            else:
                result += reverse[ch.lower()]
        else:
            result += ch
    return result


for i in (1, 2, 3):
    # open the file next to this script (not the current folder)
    with open(os.path.join(BASE, f"test_ciphertext_{i}.txt")) as f:
        ciphertext = f.read()

    print(f"===== Question {i} =====")
    print(decrypt(ciphertext))
    print()
