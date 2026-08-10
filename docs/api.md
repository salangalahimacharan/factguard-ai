# FactGuard AI API Reference Documentation

## Endpoints Summary

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check & provider status |
| `POST` | `/fact-check` | Execute multi-agent fact check on raw text |
| `POST` | `/fact-check/url` | Scrape target article URL & verify claims |
| `POST` | `/fact-check/image` | Extract text via OCR from post screenshot & verify |
| `GET` | `/fact-check/history` | Retrieve past fact-check reports list |
| `GET` | `/fact-check/{id}` | Get complete fact-check report by ID |
| `GET` | `/fact-check/{id}/pdf` | Download report as academic PDF |
| `GET` | `/fact-check/demo-claims` | Get 10 pre-configured academic demo test cases |
| `GET` | `/evaluations` | System evaluation metrics & analytics |

## Example Request (POST /api/v1/fact-check)
```json
{
  "input_text": "NASA's James Webb Space Telescope detected atmospheric water vapor on an exoplanet in 2023.",
  "input_type": "text"
}
```
