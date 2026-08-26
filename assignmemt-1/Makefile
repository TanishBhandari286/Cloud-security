PYTHON = python3

# Override on the command line, e.g.:
#   make decrypt FILE=ciphertext-2.txt OPTS="--seed 311"
FILE  ?= ciphertext-1.txt
OPTS  ?=

solve:
	$(PYTHON) solver.py $(FILE) $(OPTS)

extract:
	$(PYTHON) extractKey.py $(FILE) $(OPTS)

decrypt:
	$(PYTHON) decryptText.py $(FILE) $(OPTS)

clean:
	rm -rf __pycache__
	rm -f *.pyc
