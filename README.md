# Comparative Pricing Agent (RAG)

This project provides a lightweight comparative agent that fetches product pages, retrieves relevant content with RAG, and compares prices across sites to find where a product is priced lowest globally.

## Quick start

```bash
python -m comparative_agent --help
```

Example usage:

```bash
python -m comparative_agent "Nintendo Switch OLED" \
  --urls "https://example.com/product1" "https://example.com/product2" \
  --base-currency USD
```

## FastAPI (local or Colab)

Run an API server locally:

```bash
uvicorn comparative_agent.asgi:app --reload --port 8000
```

Example request:

```bash
curl -X POST "http://localhost:8000/compare" \
  -H "Content-Type: application/json" \
  -d '{"product":"Nintendo Switch OLED","urls":["https://example.com/product1","https://example.com/product2"],"base_currency":"USD"}'
```

## Colab

Open `notebooks/comparative_agent_colab.ipynb` in Google Colab and follow the instructions to install dependencies and run the agent.
