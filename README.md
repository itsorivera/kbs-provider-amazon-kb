# Amazon KB Provider Service

This microservice is responsible for connecting and managing retrieval queries to **Amazon Bedrock Knowledge Bases**. It is designed following a **Clean Architecture** to decouple domain logic from infrastructure details.

## 🏗️ Architecture

The project is part of a larger architecture that includes a **Gateway** service and **Provider** services. The **Gateway** service is responsible for receiving requests and forwarding them to the **Provider** service, which is responsible for connecting to the **Amazon Bedrock Knowledge Bases** and returning the results.

![Architecture](assets/architecture.jpeg)

## 🚀 Installation and Execution

This project uses `uv` for dependency management.

1.  **Install dependencies**:

    ```bash
    uv sync
    ```

2.  **Configure environment variables**:
    Create a `.env` file or define the following variables:

    ```env
    AWS_REGION=us-west-2
    AWS_PROFILE=default  # Optional
    KNOWLEDGE_BASE_TAG_KEY=mcp-multirag-kb
    ```

3.  **Run the service**:
    ```bash
    uv run uvicorn src.app:create_app --reload
    ```

## 📋 API Contract (Endpoints)

The service exposes the following endpoints as required by the Gateway contract:

### `GET /knowledge-bases`

Lists available knowledge bases that have the configured tag (default: `mcp-multirag-kb=true`).

### `POST /retrieve`

Performs a retrieval query to get raw chunks from a specific knowledge base.

**Request Body:**

```json
{
  "query": "your query",
  "knowledge_base_id": "KB_ID",
  "num_results": 20,
  "reranking": false,
  "filter": {
    "equals": {
      "key": "metadata_key",
      "value": "metadata_value"
    }
  }
}
```

### `POST /retrieve-and-generate`

Performs a retrieval and uses an LLM to generate a natural language response based on the findings.

**Request Body (with advanced filters):**

```json
{
  "knowledge_base_id": "KB_ID",
  "query": "your query",
  "num_results": 5,
  "reranking": true,
  "filter": {
    "andAll": [
      {
        "equals": {
          "key": "desired_destination",
          "value": "Bali, Indonesia"
        }
      },
      {
        "greaterThan": {
          "key": "rating",
          "value": 4
        }
      }
    ]
  }
}
```

> **Note:** For `retrieve-and-generate`, the maximum value for `num_results` allowed by Bedrock is 5.

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastAPI**: High-performance web framework.
- **Uvicorn**: ASGI server implementation for FastAPI.
- **Boto3**: AWS SDK for Python.

---

_Developed as part of the AI Portfolio by [itsorivera](https://github.com/itsorivera)._
