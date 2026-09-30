install:
	pip install -e '.[dev]'

run:
	uvicorn app.main:app --reload

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(m)"

test:
	pytest

lint:
	ruff check .

format-check:
	ruff format --check .
