import asyncio
import os
import re
import time
from dotenv import load_dotenv
load_dotenv()

MODEL = "gemini-3.1-flash-lite"  # best free model on AI Studio
MAX_SEARCH_USES = 5
CONCURRENT_REQUESTS = 2  # keep low to avoid rate limits
MAX_RETRIES = 5
INITIAL_BACKOFF = 3  # seconds

SYSTEM_PROMPT = """You are an elite financial analyst with deep expertise in:
- SEC filings (10-K, 10-Q, 8-K, proxy statements)
- Financial modeling (LBO, DCF, EBITDA bridges, accretion/dilution)
- Equity research (EPS beats/misses, guidance tracking, KPI analysis)
- Capital markets (M&A deal terms, premiums, convertible notes)
- Stock price performance and market data

CRITICAL RULES — your score depends on these:
1. Always include EXACT numbers with units ($M, $B, %, bps, x multiples)
2. Show intermediate calculation steps before the final answer
3. For rankings/comparisons, list ALL companies with values, ranked explicitly
4. For beat/miss questions, state the exact dollar or bps difference
5. For multi-part questions (i, ii, iii, iv), answer EVERY part with a labeled header
6. Go to 2 decimal places on percentages (e.g. 14.56% not ~15%)
7. For basis points: state direction clearly (e.g. "increased 410bps")
8. End every answer with a direct conclusion sentence

Always use Google Search to find:
- Current and historical stock prices on specific dates
- SEC filings on SEC EDGAR (10-K, 10-Q, 8-K)
- M&A announcement press releases
- Earnings call transcripts and guidance figures
- Any data tied to a specific date or filing
"""


def _log(msg: str) -> None:
    import sys
    print(msg, file=sys.stderr, flush=True)


async def run_batch(inputs: list[str], api_key: str) -> list[str]:
    if not api_key:
        return ["unknown"] * len(inputs)

    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    total = len(inputs)

    async def _call(idx: int, inp: str) -> str:
        async with semaphore:
            _log(f"[{idx+1}/{total}] Starting: {inp[:80]}{'...' if len(inp) > 80 else ''}")
            result = await _call_gemini(inp, api_key)
            _log(f"[{idx+1}/{total}] Done ({len(result)} chars)")
            return result

    # Stagger launches slightly to avoid burst rate limits
    tasks = []
    for idx, inp in enumerate(inputs):
        tasks.append(asyncio.ensure_future(_call(idx, inp)))
        await asyncio.sleep(0.5)  # small stagger between launches

    return list(await asyncio.gather(*tasks))


async def _call_gemini(question: str, api_key: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0,
        max_output_tokens=8192,
        thinking_config=types.ThinkingConfig(
            thinking_budget=8000,  # deep reasoning for complex finance questions
        ),
    )

    loop = asyncio.get_event_loop()

    for attempt in range(MAX_RETRIES):
        try:
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=MODEL,
                    contents=question,
                    config=config,
                ),
            )
            return (response.text or "No answer generated.").strip()
        except Exception as exc:
            err_text = str(exc).lower()
            is_rate_limit = any(
                tok in err_text
                for tok in ("429", "rate", "quota", "resource_exhausted", "too many requests", "retrydelay")
            )
            if not is_rate_limit or attempt >= MAX_RETRIES - 1:
                _log(f"ERROR (attempt {attempt+1}/{MAX_RETRIES}): {exc}")
                raise

            # Parse retry delay from error if available
            delay_match = re.search(r"retrydelay.*?(\d+)s", err_text)
            wait = int(delay_match.group(1)) if delay_match else INITIAL_BACKOFF * (2 ** attempt)
            wait = min(wait, 60)
            _log(f"Rate limited (attempt {attempt+1}/{MAX_RETRIES}), retrying in {wait}s...")
            await asyncio.sleep(wait)

    return "Error: max retries exceeded"


if __name__ == "__main__":
    import json
    import sys

    inputs_file = sys.argv[1]
    with open(inputs_file) as f:
        data = json.load(f)

    # Support both plain list of strings AND list of {"input": ...} dicts
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict):
            inputs = [item["input"] for item in data]
        else:
            inputs = data
    else:
        inputs = data

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Running {len(inputs)} questions with {MODEL}...", file=sys.stderr)
    predictions = asyncio.run(run_batch(inputs, api_key))
    print(json.dumps(predictions, indent=2))