# Medscrape

Medscrape is an open source Python project that takes in URLs, scrapes an entire website, uses the unstructured library to process the data, stores and embeds it using serverless instance of lanceDB, and then uses the instructor library to make API calls to OpenAI for inference over the data.

## Features

- Scrapes entire websites by following internal links.
- Use the unstructured library to partitioning and processing the data.
- Store extracted data in lanceDB for fast retrieval and embeddings.
- Make API calls to OpenAI or locally using Ollama for inference over the stored data.
- Access functionality and stored content through a RESTful API built with FastAPI.

## Prerequisites

- Docker and docker-compose (for Docker setup)
- Python 3.9+ and Redis (for local setup)
- Poetry for dependency management

## Installation

### Local Setup with Poetry

1. Clone the repository:

    ```
    git clone https://github.com/greyhaven-ai/medscrape.git
    ```

2. Navigate to the project directory:

    ```
    cd medscrape
    ```
3. Install Poetry for dependency management:
   ```
   pip install poetry
   ```
4. Install the required dependencies:
   ```
   poetry install
   ```

5. Make sure Redis is running on your machine.
4. Rename `.env.example` to `.env` and add the correct API keys.

### Using Docker

1. Clone the repository and navigate to the directory as above.
2. Build the Docker image:
   ```
   docker build -t medscrape .
   ```
3. Run the Docker container, ensuring that the `.env` file is correctly set up with the necessary API keys:
   ```
   docker run -d -p 8000:8000 medscrape
   ```

## Usage

The project exposes new main endpoints through FastAPI:

### Run a Scraping and Processing Job

- **POST** `/run/`

  Initiates the scraping and processing of a website specified by the top-level domain (TLD) and processes user questions over the scraped data.

  Accepts a JSON body with a `tld` field specifying the top-level domain of the website to scrape and a `questions` field for the list of questions for which answers are sought from the scraped content.

  Example request:
  ```json
  {
    "tld": "https://med.stanford.edu",
    "questions": ["What were the Medical School's top scientific advancements of 2023?", "Who is on the leadership team of the Medical School?"]
  }
  ```

  Example response:
  ```json
  {
    "message": "Completed processing and answering questions.",
    "data": [
      {
        "question": "What were the Medical School's top scientific advancements of 2023?",
        "answer": "Example answer 1"
      },
      {
        "question": "Who is on the leadership team of the Medical School?",
        "answer": "Example answer 2"
      }
    ]
  }
  ```

### Process Scraped Data

- **POST** `/process/`

  Initiates the scraping and processing of a single URL. This endpoint is designed to scrape the specified URL, follow internal links within the same top-level domain (TLD), and process the content found.

  Example request:
  ```json
  {{
    "url": "https://med.stanford.edu"
  }
  ```

  Example response:
  ```json
  {
    "message": "Processing completed",
    "url": "https://med.stanford.edu",
    "urls_found": 120
  }
  ```

### Query Stored Data

- **POST** `/query/`

  This endpoint allows users to submit a top-level domain (TLD) and a list of questions, then receive answers based on the data processed and stored. It uses LLMs to infer answers from the processed website data.

  Example response:
  ```json
  {
    "tld": "https://med.stanford.edu",
    "questions": ["What is the main research focus of the lab?", "Who leads the research team?"]
  }
  ```
  Example response:
  ```json
    {
    "message": "Inference call made successfully",
    "data": [
      {
        "question": "What is the main research focus of the lab?",
        "answer": "The main research focus is on genetic mutations affecting longevity."
      },
      {
        "question": "Who leads the research team?",
        "answer": "The research team is led by Dr. Jane Doe."
      }
    ]
  }
  ```


## Configuration

The project can be configured through environment variables, which are set in the `.env` file for local development and in the `Dockerfile` for Docker deployments.

- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`: Redis connection settings.
- `FASTAPI_HOST`, `FASTAPI_PORT`: FastAPI server settings.
- `LANCE_DB_URI`: LanceDB data directory.
- `OPENAI_API_KEY`: OpenAI API key for working with OpenAI models.

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is open source and available under the [MIT License](LICENSE).


