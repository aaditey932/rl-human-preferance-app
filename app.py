"""Human-in-the-Loop RL: collect prompt, two responses, and human preference."""

import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from data import (
    append_record,
    create_record,
    export_full_jsonl,
    export_training_jsonl,
    get_random_prompt_from_dataset,
)
from db import fetch_all_preferences, insert_preference, is_configured as db_configured
from llm import generate_two_responses

# Config (can move to env or config file)
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.environ.get("OPENAI_MAX_TOKENS", "1024"))
RESPONSE_CHAR_LIMIT = int(os.environ.get("RESPONSE_CHAR_LIMIT", "500"))
PERSIST_JSONL = Path(__file__).resolve().parent / "preferences.jsonl"


def init_session_state():
    if "records" not in st.session_state:
        if db_configured():
            try:
                st.session_state.records = fetch_all_preferences()
            except Exception:
                st.session_state.records = []
        else:
            st.session_state.records = []
    if "response_a" not in st.session_state:
        st.session_state.response_a = None
    if "response_b" not in st.session_state:
        st.session_state.response_b = None
    if "generation_metadata" not in st.session_state:
        st.session_state.generation_metadata = None
    if "prompt_for_round" not in st.session_state:
        st.session_state.prompt_for_round = None
    if "prompt_input" not in st.session_state:
        st.session_state.prompt_input = ""
    if "preference_saved_to_supabase" not in st.session_state:
        st.session_state.preference_saved_to_supabase = False


def clear_current_round():
    st.session_state.response_a = None
    st.session_state.response_b = None
    st.session_state.generation_metadata = None
    st.session_state.prompt_for_round = None


def record_preference(preference: str):
    if st.session_state.response_a is None or st.session_state.response_b is None:
        return
    meta = dict(st.session_state.generation_metadata or {})
    meta["timestamp"] = datetime.utcnow().isoformat() + "Z"
    prompt = st.session_state.prompt_for_round
    response_a = st.session_state.response_a
    response_b = st.session_state.response_b
    if db_configured():
        try:
            insert_preference(prompt, response_a, response_b, preference, meta)
        except Exception as e:
            err_msg = str(e)
            detail = getattr(e, "message", None) or getattr(e, "details", None)
            if detail:
                err_msg = f"{err_msg} — {detail}"
            st.error(f"Failed to save to database: {err_msg}")
            return
        st.session_state.preference_saved_to_supabase = True
        record = create_record(prompt, response_a, response_b, preference, meta)
        st.session_state.records.append(record)
        clear_current_round()
    else:
        append_record(
            st.session_state.records,
            prompt,
            response_a,
            response_b,
            preference,
            meta,
            jsonl_path=PERSIST_JSONL,
        )
        clear_current_round()


def main():
    init_session_state()
    st.set_page_config(page_title="Human-in-the-Loop RL", page_icon="🔄")
    st.title("Human-in-the-Loop RL — Preference Collection")
    st.caption("Enter a prompt, get two model responses, then choose which you prefer (or a tie).")
    st.info(f"**Response limit:** {RESPONSE_CHAR_LIMIT} characters — model responses are instructed to stay within this length.")

    if st.session_state.preference_saved_to_supabase:
        st.success("Preference saved to Supabase.")
        st.session_state.preference_saved_to_supabase = False

    # Prompt input and generate
    prompt_value = (st.session_state.prompt_for_round or "") if st.session_state.response_a is not None else st.session_state.prompt_input
    prompt = st.text_area(
        "Prompt",
        value=prompt_value,
        height=120,
        placeholder="Enter your prompt here, or load one from the dataset below.",
        disabled=(st.session_state.response_a is not None),
    )
    if st.session_state.response_a is not None:
        prompt = st.session_state.prompt_for_round or ""
    else:
        st.session_state.prompt_input = prompt

    col_load, col_gen, _ = st.columns([1, 1, 2])
    with col_load:
        load_random_clicked = st.button(
            "Load random prompt from dataset",
            disabled=(st.session_state.response_a is not None),
            help="Load one of 23 ambiguous-ethical prompts (tradeoffs, no single right answer).",
        )
    with col_gen:
        generate_clicked = st.button(
            "Generate two responses",
            disabled=(st.session_state.response_a is not None),
        )

    if load_random_clicked:
        try:
            st.session_state.prompt_input = get_random_prompt_from_dataset()
            st.rerun()
        except Exception as e:
            st.error(f"Could not load dataset: {e}")

    if generate_clicked:
        if not prompt.strip():
            st.warning("Please enter a prompt first.")
        else:
            with st.spinner("Generating two responses..."):
                try:
                    a, b, meta = generate_two_responses(
                        prompt.strip(),
                        model=MODEL,
                        temperature=TEMPERATURE,
                        max_tokens=MAX_TOKENS,
                        response_char_limit=RESPONSE_CHAR_LIMIT,
                    )
                    st.session_state.response_a = a
                    st.session_state.response_b = b
                    st.session_state.generation_metadata = meta
                    st.session_state.prompt_for_round = prompt.strip()
                except Exception as e:
                    st.error(f"Generation failed: {e}")
            st.rerun()

    # Show responses and preference buttons (fixed once generated)
    if st.session_state.response_a is not None and st.session_state.response_b is not None:
        st.subheader("Responses (choose your preference)")

        panel_a = st.container(border=True)
        with panel_a:
            st.markdown("**Response A**")
            st.text_area("Response A", value=st.session_state.response_a, height=200, disabled=True, key="disp_a", label_visibility="collapsed")

        panel_b = st.container(border=True)
        with panel_b:
            st.markdown("**Response B**")
            st.text_area("Response B", value=st.session_state.response_b, height=200, disabled=True, key="disp_b", label_visibility="collapsed")

        pref_a, pref_b, pref_tie = st.columns(3)
        with pref_a:
            if st.button("Prefer A"):
                record_preference("a")
                st.rerun()
        with pref_b:
            if st.button("Prefer B"):
                record_preference("b")
                st.rerun()
        with pref_tie:
            if st.button("Tie"):
                record_preference("tie")
                st.rerun()

    # History table
    st.subheader("Recorded preferences")
    if not st.session_state.records:
        st.info("No preferences recorded yet. Generate responses and choose A, B, or Tie.")
    else:
        rows = []
        for i, r in enumerate(st.session_state.records):
            rows.append({
                "#": i + 1,
                "Prompt (preview)": (r["prompt"][:50] + "…") if len(r["prompt"]) > 50 else r["prompt"],
                "Preference": r["preference"],
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

    # Export
    st.subheader("Export preference data")
    training_jsonl = export_training_jsonl(st.session_state.records)
    full_jsonl = export_full_jsonl(st.session_state.records)
    col_tr, col_full = st.columns(2)
    with col_tr:
        st.download_button(
            "Download training JSONL (prompt, chosen, rejected)",
            data=training_jsonl,
            file_name="preferences_training.jsonl",
            mime="application/jsonl",
        )
    with col_full:
        st.download_button(
            "Download full JSONL (all fields + metadata)",
            data=full_jsonl,
            file_name="preferences_full.jsonl",
            mime="application/jsonl",
        )


if __name__ == "__main__":
    main()
