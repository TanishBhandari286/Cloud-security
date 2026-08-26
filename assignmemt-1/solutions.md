# Assignment 1 — Solutions

**Name:** Tanish Bhandari
**Roll No:** 23csu311

---

## Problem statement

We are given two ciphertext files. Both were produced by the same
monoalphabetic substitution cipher:

- Plaintext is ordinary lowercase English (letters `a`–`z`).
- Every plaintext letter is replaced by **one fixed symbol** from the
  cipher alphabet `1234567890@#$zyxwvutsrqpon` (26 symbols).
- Spaces and punctuation are **not** encrypted — they are kept as-is and
  act as structural anchors.

The secret key was not provided, so both files had to be broken using
cryptanalysis only.

---

## Question 1 — `ciphertext-1.txt`

### Recovered plaintext

> india, officially the republic of india, is a country in south asia. it
> is the seventh largest country by area, the second most populous
> country, and the most populous democracy in the world. bounded by the
> indian ocean on the south, the arabian sea on the southwest, and the
> bay of bengal on the southeast, it shares land borders with pakistan to
> the west; china, nepal, and bhutan to the north; and bangladesh and
> myanmar to the east. in the indian ocean, india is in the vicinity of
> sri lanka and the maldives; its andaman and nicobar islands share a
> maritime border with thailand, myanmar and indonesia. good, now turn
> for the second part of the question, good luck!

The passage is about **India** — its geography, neighbours and the oceans
that surround it. The last line ("good, now turn for the second part of
the question, good luck!") confirms the second file is part of the same
assignment.

**Recovered key** (cipher symbol for `a`–`z`):

```
y5n8@p7q1twu09$342vos6#zxr
```

---

## Question 2 — `ciphertext-2.txt`

### Recovered plaintext

> defeated and leaving his dinner untouched, he went to bed. that night he
> did not sleep well, having feverish dreams, having no rest. he was
> unsure whether he was asleep or dreaming. conscious, unconscious, all
> was a blur. he remembered crying, wishing, hoping, begging, even
> laughing. he floated through the universe, seeing stars, planets,
> seeing earth, all but himself. when he looked down, trying to see his
> body, there was nothing. it was just that he was there, but he could
> not feel anything for just his presence.

The passage is a short **narrative about a feverish dream** — a man who
cannot sleep, drifts between being conscious and unconscious, and finally
sees himself from outside, as a presence with no body.

**Recovered key** (cipher symbol for `a`–`z`):

```
8ot64spnrxzqwy$173vu205@#9
```

---

## My first attempt — why it failed

My first idea was **pure frequency analysis**: count how often each cipher
symbol appears, sort the symbols by frequency, and map the most frequent
symbols to the most frequent English letters (`e`, `t`, `a`, `o`, `i`,
`n`, `s`, ...). This is the classic textbook approach.

I wrote a script that did exactly that and decrypted both files. The
output looked *almost* right — the structure was there, the word lengths
matched, common short words were recognisable — but the text was **still
garbage**:

- `india` kept coming out as something like `iusda` or `iwfka` — the
  first letter was right, the rest wrong.
- Longer words were completely mangled because the frequency ranks of the
  *middle* letters (`t` vs `d` vs `l`) are too close, so a symbol can be
  mis-assigned by one or two positions.

**Why it failed:** frequency analysis only works reliably for the top few
letters. The remaining 20 letters have very similar frequencies, so a
greedy rank-to-rank match gets many of them wrong, and every wrong letter
cascades into wrong words. With no way to *fix* mistakes, the result was
unreadable.

---

## The solution — frequency seed + simulated annealing

The fix was to treat the frequency-based mapping as a **starting point,
not the answer**, and then let a search algorithm improve it:

### Step 1 — Seed the key

Count symbol frequencies in the ciphertext and match them against letter
frequencies computed from a generic English corpus. This gives a decent
first key (most common symbols right, the rest likely wrong).

### Step 2 — Score a candidate plaintext

Any key can be applied to the ciphertext to produce a candidate
plaintext. Each candidate is scored with:

- **Character n-gram likelihood** — bigram and trigram log-probabilities
  built from the same English corpus. English has very strong bigram/
  trigram habits (`th`, `he`, `ing`, `tion`...), so a correctly decrypted
  text scores dramatically higher than a wrong one.
- **Common-word bonus** — words like `the`, `and`, `india` get a bonus.
- **Structural penalties** — impossible English structures are punished
  (e.g. `q` not followed by `u`, or runs of 6+ consonants).

### Step 3 — Simulated annealing

Start from the frequency-seeded key and repeatedly try **swapping two
symbols** in the key. If the swap improves the score, keep it; if not,
keep it with a probability that shrinks as a "temperature" cools down
(polynomial cool-down here). This lets the search escape local optima
that would trap a plain hill-climber. The whole process is repeated from
several random starting keys and the best result is kept.

### Result

Both ciphertexts decrypt to clean, readable English (shown above). The
recovery is reproducible:

```sh
python3 decryptText.py ciphertext-1.txt --seed 311
python3 decryptText.py ciphertext-2.txt --seed 311
```

### Lessons learned

1. Frequency analysis alone is not enough — the mid-frequency letters are
   too close together to rank reliably.
2. Scoring matters more than the initial guess: as long as the scorer
   rewards English-like text, a search over key swaps converges to the
   correct key.
3. Random restarts make the result robust — one annealing run can get
   stuck, many runs cannot.

---

## How to run the code

```sh
# Decrypt a file (prints the plaintext)
python3 decryptText.py ciphertext-1.txt

# Print only the recovered key
python3 extractKey.py ciphertext-1.txt

# Full solver with progress output and custom settings
python3 solver.py ciphertext-2.txt --verbose --iterations 30000 --restarts 10 --seed 311

# Or via make
make decrypt FILE=ciphertext-1.txt
make extract FILE=ciphertext-2.txt
```

Note: the solver is stochastic by default (random restarts), so different
runs may produce slightly different keys; use `--seed 311` for a fully
reproducible run. If a run comes out imperfect, simply run it again — the
best run wins.
