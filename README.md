# Human-in-the-Loop RL — Preference Collection App

A simple Streamlit app that collects human preference data for downstream RLHF-style training: you enter a prompt, the app generates two responses from the same OpenAI model, and you choose which you prefer (or mark a tie). All data can be exported as `{prompt, chosen, rejected}` pairs.

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set your OpenAI API key**

   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

   (Or use a `.env` file and load it before running; the OpenAI client reads `OPENAI_API_KEY` from the environment.)

## Run the app

From the Lab 6 directory:

```bash
streamlit run app.py
```

## How to use

1. Enter a **prompt** in the text area and click **Generate two responses**.
2. Once generated, **Response A** and **Response B** are fixed. Choose **Prefer A**, **Prefer B**, or **Tie**.
3. Your choice is recorded; you can then enter a new prompt and repeat.
4. Use **Export** to download:
   - **Training JSONL**: only non-tie rows as `{"prompt": "...", "chosen": "...", "rejected": "..."}` for reward-model or preference training.
   - **Full JSONL**: all records including metadata (model, temperature, timestamp) and ties.

## Using the export for training

- **Training file** (`preferences_training.jsonl`): one JSON object per line with `prompt`, `chosen`, and `rejected`. Use this for reward model fitting or DPO/RLHF pipelines that expect preference pairs. Ties are omitted.
- **Full file**: use for debugging or if you want to include ties (e.g. with a `preference` field) or metadata in your pipeline.

## Optional environment variables

- `OPENAI_MODEL` — default: `gpt-4o-mini`
- `OPENAI_TEMPERATURE` — default: `0.7`
- `OPENAI_MAX_TOKENS` — default: `1024`

Preference records are also appended to `preferences.jsonl` in the project directory as you submit choices.
