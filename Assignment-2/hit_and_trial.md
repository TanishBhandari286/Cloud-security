# Hit and trial method (n-grams approach)

**Name:** Tanish Bhandari
**Roll No:** 23csu311

## what is an n-gram

an n-gram is simply n characters coming together in a text. for example:

- bigram (2 characters) - "th", "he", "in", "an"
- trigram (3 characters) - "the", "ing", "and", "ion"
- tetragram (4 characters) - "tion", "that", "ther"

some n-grams appear very often in english and some almost never appear. for example "th" is everywhere but "xz" basically never happens. these habits of english are very strong and that is what we use.

## the main idea

when we decode a ciphertext with a wrong key, the output is random junk, so its n-grams are unusual and rare. but when we decode with the correct key, the output is proper english, so its n-grams are the common ones.

so the trick is this - we can give a score to any guessed key:

1. decode the whole file with that key
2. check how common the n-grams of the decoded text are
3. higher score means the text looks more like english

## how the scoring works

we built a table of n-gram probabilities from a sample of normal english text. then for every n-gram in the candidate text we add its probability (we use log probabilities so that we can add them instead of multiplying, which is easier for the computer). n-grams which are not in our table get a small penalty value instead of zero.

we also added two more things to the score:

- bonus for very common words like "the", "and", "of"
- penalty for impossible english structures, like a "q" which is not followed by "u", or a word with 6 consonants in a row

## the hit and trial (search)

this is the actual "hit and trial" part:

1. start with a rough key - we make a first guess using frequency analysis, meaning the most common symbol of the ciphertext gets the most common english letter
2. try a small change - swap two symbols of the key
3. decode the file with the new key and score it
4. if the score went up, keep the change. if the score went down, we usually undo it, but in the beginning we sometimes keep it anyway (this is called the temperature / simulated annealing part). keeping a bad change sometimes is important because it lets us escape from a half-right key which looks good but is wrong
5. repeat this thousands of times and slowly stop accepting the bad changes
6. do the whole thing from a few random starting keys and keep the best result

## why it works

the correct key makes the whole text fully english, so its score is very high. any wrong key leaves junk somewhere, so its score is much lower. so even though we are just randomly hitting and trying swaps, the score always guides us towards the correct key. the search is like climbing a hill in fog - you cannot see the top but you can feel whether the ground is going up or down.

## example from our assignment

in our files "oq@" appears many times as a 3 letter word. the trigram "the" is one of the most common trigrams in english, so the score heavily rewards the key which maps o=t, q=h, @=e. once that happens the text starts looking like english and the rest of the key gets fixed one swap at a time.

the actual code is in solver.py of assignment 1. it uses bigram and trigram probabilities with weights, the common word bonus and the structural penalties, and it improves the key with the swap and score loop described above.

## one line summary

n-grams tell us "how english does this text look" and the hit and trial loop keeps changing the key until that english score cannot get any better - and the key which makes the text most english is the correct key.
