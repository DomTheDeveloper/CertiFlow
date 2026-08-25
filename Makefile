.PHONY: test bench

test:
	python -m pytest -q

bench:
	certiflow benchmark --nodes 1000
