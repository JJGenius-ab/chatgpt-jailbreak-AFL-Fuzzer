# AFL Jailbreak Fuzzer

This project mutates seed prompts and evaluates whether an LLM response changes in interesting or unsafe ways.

The main entrypoint is `fuzzer.py`. It is safe-by-default: running it without flags only prints generated prompt mutation metadata and does not send anything to an LLM.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For live LLM evaluation, set a Gemini API key:

```bash
export GOOGLE_API_KEY="your-key-here"
```

Optionally set a model:

```bash
export GEMINI_MODEL="gemini-2.5-flash"
```

Never commit `.env` files or API keys.

## Safe Dry Run

```bash
python3 fuzzer.py
```

This prints mutation metadata only. To inspect the full generated prompts locally, add `--show-prompts`.

## Live Evaluation

```bash
python3 fuzzer.py --live --max-prompts 3 --max-mutations-per-prompt 4
```

Live mode sends generated prompts to the configured LLM and appends interesting results to `outputs/logs.jsonl`.

## Project Structure

- `fuzzer.py`: safe-by-default command-line fuzzer.
- `fuzzer2.py`, `fuzzer3.py`: legacy wrappers that delegate to `fuzzer.py`.
- `mutations/`: prompt mutation strategies.
- `evaluation/`: response rating, jailbreak checks, and semantic drift scoring.
- `utils/llm_api.py`: Gemini API wrapper using environment variables.
- `prompts/`: seed prompts and bypass dictionaries.
- `outputs/`: generated JSONL logs.
- `results/`: historical CSV outputs from previous experiment runs.
- `docs/`: notebook and presentation materials.
- `assets/`: images used by documentation or presentations.

## Notes

- `sentence-transformers` and `torch` are only needed for cosine drift detection.
- Some mutation strategies use the LLM itself and therefore only run in `--live` mode.
- Historical CSV outputs live in `results/`.
