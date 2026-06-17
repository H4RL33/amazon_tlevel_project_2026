FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry==1.8.5

ENV POETRY_VIRTUALENVS_IN_PROJECT=1

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction --without dev

COPY . .

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
