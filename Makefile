.PHONY: help test lint report add

help:
	@grep -E '^##' Makefile | sed 's/## //'

## test: run the test suite
test:
	python -m pytest -q

## report: print the weekly pipeline report
report:
	python -m jobtrack report

## stats: print pipeline metrics as a table
stats:
	python -m jobtrack stats

## validate: check every record in the data file
validate:
	python -m jobtrack validate
