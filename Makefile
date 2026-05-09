.PHONY: install lint typecheck test run

install:
	pip install -e .[dev]

lint:
	ruff check .

typecheck:
	mypy app

test:
	pytest

run:
	uvicorn app.main:app --reload
