# Use an official Python runtime as a parent image
FROM python:3.11-slim AS base

RUN apt-get update && apt-get install -y gcc python3-dev libgl1-mesa-glx libglib2.0-0

COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Set PYTHONPATH environment variable to include the directory where the medscrape module is located
ENV PYTHONPATH "${PYTHONPATH}:/app/backend"

FROM base AS final
WORKDIR /app
COPY . .

EXPOSE 8000
CMD ["uvicorn", "medscrape.main:app", "--host", "0.0.0.0", "--port", "8000"]
