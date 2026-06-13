# AI Financial Analyst Agent

An autonomous AI agent that answers complex financial questions using Google's Gemini API with built-in Google Search for real-time data retrieval.

## Overview

This agent leverages **Gemini 3.1 Flash Lite** with deep reasoning capabilities to analyze SEC filings, financial models, equity research, and capital markets data. It uses Google Search grounding to retrieve current and historical financial information.

## Features

- **Deep Financial Expertise**: Handles SEC filings (10-K, 10-Q, 8-K), financial modeling (LBO, DCF, EBITDA), equity research, and M&A analysis
- **Google Search Integration**: Automatically searches for real-time stock prices, SEC filings, earnings data, and press releases
- **Thinking Mode**: Uses extended thinking budget (8,000 tokens) for complex multi-step financial calculations
- **Concurrent Processing**: Processes multiple questions in parallel with rate-limit-aware retry logic
- **Robust Error Handling**: Exponential backoff with automatic retries on API rate limits

## Setup

### 1. Install Dependencies

```bash
pip install google-genai python-dotenv
```

### 2. Configure API Key

Create a `.env` file in the project root:

```
GOOGLE_API_KEY=your_api_key_here
```

Get a free API key at [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 3. Run the Agent

```bash
python agent.py test.json > submission.json
```

## Input Format

The agent accepts a JSON file containing either:

- A list of question strings: `["question1", "question2", ...]`
- A list of objects: `[{"input": "question1"}, {"input": "question2"}, ...]`

## Output

The agent outputs a JSON array of answers to stdout:

```json
[
  "Detailed answer to question 1...",
  "Detailed answer to question 2..."
]
```

## Project Structure

```
├── agent.py                 # Main agent script
├── eval.py                  # Evaluation script
├── test.json                # Test questions
├── train.json               # Training questions
├── submission.json          # Generated answers
├── submission_example.json  # Example submission format
├── .env                     # API key (not committed)
└── README.md
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MODEL` | `gemini-3.1-flash-lite` | Gemini model to use |
| `CONCURRENT_REQUESTS` | `2` | Max parallel API calls |
| `MAX_RETRIES` | `5` | Retry attempts on rate limits |
| `INITIAL_BACKOFF` | `3s` | Initial retry delay |

## License

MIT
