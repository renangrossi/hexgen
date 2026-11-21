# hexgen — rebuild the table library from your PDFs, then roll regions.
# RPG_ROOT is the folder that holds Shadowdark/, OSR/ … (default: three levels up).
PY ?= python3
RPG_ROOT ?= $(abspath ../../..)
export RPG_ROOT

.PHONY: data extract curate check region region-ose clean
data: extract curate check            ## full rebuild of data/gen from the PDFs
extract:                              ## raw/*.json from every source (skips ones already there)
	$(PY) -I tools/extract_all.py
reextract:                            ## force a fresh extraction of everything
	$(PY) -I tools/extract_all.py --force
curate:                               ## raw/ → data/gen/*.yaml with stable ids
	$(PY) tools/curate.py raw data
check:                                ## every table rolls
	$(PY) -m hexgen check
test:
	$(PY) -m unittest discover -s tests -v
region:                               ## a Shadowdark region (add SEED=…)
	$(PY) -m hexgen $(if $(SEED),--seed $(SEED)) region --system sd --pdf
region-ose:                           ## the same for Old-School Essentials
	$(PY) -m hexgen $(if $(SEED),--seed $(SEED)) region --system ose --pdf
clean:
	rm -rf out __pycache__ */__pycache__ */*/__pycache__
