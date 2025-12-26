# Design Analysis API

FastAPI server that analyzes ChatGPT Vision text output and categorizes design feedback.

## Features

- **POST /analyze** - Analyzes design feedback text and returns:
  - Overall score (0-100)
  - Category scores (contrast, spacing, alignment, hierarchy)
  - Categorized issues by severity (critical, warning, info)
  - Actionable suggestions

- **GET /health** - Health check endpoint

## Installation

```bash
pip install -r requirements.txt
```

## Running Locally

```bash
uvicorn main:app --reload
```

Server will be available at `http://127.0.0.1:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Example Request

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_text": "El contraste del texto es malo y necesita mejorar. La legibilidad es crítico problema."
  }'
```

## Deployment

Ready for deployment on Render.com:
1. Push to GitHub
2. Create new Web Service on Render
3. Connect your repository
4. Render will automatically detect the Procfile

## Tech Stack

- FastAPI
- Uvicorn
- Pydantic
- Python 3.10+
