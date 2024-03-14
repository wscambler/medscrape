# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy only the files necessary for installing dependencies to avoid cache invalidation
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to not create a virtual environment inside the Docker container
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy the current directory contents into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variables
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV REDIS_DB=0
ENV REDIS_PASSWORD=
ENV FASTAPI_HOST=0.0.0.0
ENV FASTAPI_PORT=8000

# Run the FastAPI app
CMD ["uvicorn", "medscrape.main:app", "--host", "0.0.0.0", "--port", "8000"]