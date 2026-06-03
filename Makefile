.PHONY: install lint format-check test validate-codebook demo verify

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .

format-check:
	ruff format --check .

test:
	pytest -q

validate-codebook:
	python -m ifrs18_oras validate-codebook --codebook config/codebook_v0.1.0.json

demo:
	python -m ifrs18_oras demo --output-dir outputs/demo

verify: install lint format-check test validate-codebook demo
