.PHONY: install lint typecheck run

install:
	pip install -e .[dev]

lint:
	ruff check .

typecheck:
	mypy app

run:
	uvicorn app.main:app --reload
