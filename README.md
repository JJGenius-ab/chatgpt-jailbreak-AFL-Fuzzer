# Project Overview: AFL Jailbreak Fuzzer

## What This Project Does

This project is a safety-testing tool for large language models. It takes a set of seed prompts, creates mutated versions of those prompts, sends them to an LLM when live mode is enabled, and records responses that appear interesting from a safety-testing perspective.

The project is inspired by AFL-style fuzzing. Traditional fuzzers mutate inputs to discover unexpected behavior in software. This project applies the same broad idea to LLM prompts: start with known prompt patterns, generate variations, observe model behavior, and keep track of cases that produce unusual or unsafe responses.

The current implementation supports two modes:

- Dry-run mode: generates prompt mutation metadata only. This is the default and does not send prompts to an LLM.
- Live mode: sends generated prompts to the configured Gemini model and evaluates the responses.

The main entrypoint is:

```bash
python3 fuzzer.py
```

Live evaluation must be explicitly enabled:

```bash
python3 fuzzer.py --live
```

## Why I Made This Project

I made this project to explore how fuzzing ideas from software security can be adapted to LLM safety evaluation.

The goal is not to build a tool for abusing AI systems. The goal is to understand how different prompt mutation strategies affect model behavior, especially in cases where a model should refuse unsafe requests or redirect the user toward safer information.

This project helps answer questions such as:

- Which prompt transformations are more likely to change a model's response?
- Do obfuscation or reframing techniques cause different safety behavior?
- Can automated testing help find weak spots in LLM safety controls?
- How can jailbreak testing be made more systematic and reproducible?

The project also gave me a way to practice:

- Python project organization
- Async API calls
- LLM API integration
- Prompt mutation design
- Response evaluation
- Safe-by-default tooling
- GitHub project hygiene

## Design Decisions And Choices

### 1. Safe-By-Default Execution

The fuzzer runs in dry-run mode by default.

```bash
python3 fuzzer.py
```

This prints only metadata about generated mutations, such as character count and a SHA-256 fingerprint. It does not print the full prompt text by default and does not send anything to an external LLM.

Result:

- The project is safer to run accidentally.
- It avoids unnecessary API calls.
- It reduces the chance of exposing sensitive or harmful prompt text in terminal output.

To inspect full prompts locally, the user must explicitly pass:

```bash
python3 fuzzer.py --show-prompts
```

To send prompts to the LLM, the user must explicitly pass:

```bash
python3 fuzzer.py --live
```

### 2. Environment Variables For Secrets

The project reads the Gemini API key from an environment variable:

```bash
export GOOGLE_API_KEY="your-key-here"
```

The key is never printed and should never be committed to GitHub.

Result:

- API keys are not hardcoded.
- The code works outside Google Colab.
- The project is safer to publish on GitHub.

### 3. Bounded Runs

The fuzzer includes limits:

```bash
python3 fuzzer.py --max-prompts 3 --max-mutations-per-prompt 4
```

Result:

- Runs are predictable.
- API usage is easier to control.
- Testing is less likely to become expensive or unmanageable.

### 4. Modular Mutation Strategies

Mutation logic lives in the `mutations/` folder. Each mutation strategy is separated into its own file or helper module.

Examples include:

- Encoding obfuscation
- Roleplay-style reframing
- Jailbreak wrapper mutation
- Prompt substitution
- Hallucination-style masking
- Persuasive/safety-analysis framing

Result:

- Mutation strategies are easier to understand.
- New mutation types can be added without rewriting the main fuzzer.
- Individual mutation modules can be tested or modified independently.

### 5. Separate Evaluation Logic

Evaluation code lives in the `evaluation/` folder.

The project includes:

- Harmfulness scoring
- Response rating
- Jailbreak checking
- Cosine drift detection

Result:

- The fuzzer loop stays simpler.
- The scoring logic can be improved separately.
- Different evaluation methods can be swapped in later.

### 6. Legacy Entrypoints Kept As Wrappers

Older files, `fuzzer2.py` and `fuzzer3.py`, are still present, but they now delegate to the safer `fuzzer.py` workflow.

Result:

- Old references do not immediately break.
- There is only one real workflow to maintain.
- Running old entrypoints does not accidentally trigger unsafe or uncontrolled behavior.

### 7. Organized Project Artifacts

Historical outputs and supporting files were moved into labeled folders.

Result:

- The top-level directory is cleaner.
- Code files are easier to find.
- Old experiment results are preserved without cluttering the main project folder.

## Results And Observations

The project produced several historical CSV result files, now stored in:

```text
results/
```

These files represent previous experiment runs using different mutation techniques.

The main result of the project is not a single final model score. Instead, the project demonstrates a repeatable workflow for generating prompt variants, testing model responses, and recording cases that may deserve manual review.

Important observations from the design process:

- Prompt mutation can be treated similarly to input fuzzing.
- Safe defaults matter because prompt-safety research can involve sensitive content.
- A notebook is useful for experimentation, but a cleaned Python entrypoint is better for repeatable runs.
- Separating mutation, evaluation, prompts, outputs, and documentation makes the project easier to maintain.

## Setup Instructions

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set the Gemini API key if you want to use live mode:

```bash
export GOOGLE_API_KEY="your-key-here"
```

Optionally choose a Gemini model:

```bash
export GEMINI_MODEL="gemini-2.5-flash"
```

Run a safe dry run:

```bash
python3 fuzzer.py
```

Run a bounded live evaluation:

```bash
python3 fuzzer.py --live --max-prompts 3 --max-mutations-per-prompt 4
```

Show full generated prompts during dry-run mode:

```bash
python3 fuzzer.py --show-prompts
```

## Project Structure

```text
.
├── fuzzer.py
├── fuzzer2.py
├── fuzzer3.py
├── requirements.txt
├── README.md
├── PROJECT_OVERVIEW.md
├── .env.example
├── .gitignore
├── assets/
│   └── image.png
├── docs/
│   ├── CyberSecProject.ipynb
│   └── Cybersec_Project_Presentation.pptx
├── evaluation/
│   ├── cosine_drift_classifier.py
│   ├── harmful_score_classifier.py
│   ├── is_jailbreak.py
│   └── response_rating.py
├── mutations/
│   ├── encoding_obfuscation.py
│   ├── hallucination.py
│   ├── jailbreak_wrapper.py
│   ├── mutator.py
│   ├── persuasive.py
│   ├── prompt_injection.py
│   ├── roleplay_template.py
│   ├── substitution.py
│   └── synonym_replace.py
├── outputs/
│   └── generated JSONL logs
├── prompts/
│   └── seed prompts and prompt dictionaries
├── results/
│   └── historical CSV experiment outputs
└── utils/
    └── llm_api.py
```

## Main Files

### `fuzzer.py`

The main command-line tool. It loads seed prompts, generates mutations, and either prints mutation metadata or performs live LLM evaluation.

### `utils/llm_api.py`

Handles Gemini API access. It reads the API key from `GOOGLE_API_KEY` and does not print secrets.

### `mutations/`

Contains prompt mutation methods. These are the fuzzing strategies used to generate prompt variants.

### `evaluation/`

Contains response and safety evaluation helpers.

### `prompts/`

Contains seed prompts and bypass dictionaries used as input data.

### `results/`

Contains historical CSV outputs from previous experiment runs.

### `docs/`

Contains the original notebook and presentation materials.

## Safety Notes

- Dry-run mode is the default.
- Live mode must be explicitly enabled with `--live`.
- The project does not commit API keys.
- `.env` files are ignored by Git.
- Full prompts are not printed unless `--show-prompts` is used.
- Live runs should be bounded with `--max-prompts` and `--max-mutations-per-prompt`.

## Future Improvements

Potential improvements include:

- Adding unit tests for each mutation strategy.
- Adding structured configuration through a YAML or TOML file.
- Exporting summary reports after live runs.
- Adding better duplicate detection across mutation outputs.
- Adding safer offline mock mode for testing evaluation logic without API calls.
- Improving result analysis with charts or summary tables.
