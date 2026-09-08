"""
llm_client.py
--------------
Unified LLM client supporting Google Gemini, OpenAI, and Anthropic with automatic retries on rate limits and temporary traffic spikes.
"""

import os
import time
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

MODEL_GEMINI = "gemini-3.6-flash"
MODEL_ANTHROPIC = "claude-3-5-sonnet-20241022"
MODEL_OPENAI = "gpt-4o-mini"


def call_llm(system_prompt: str, messages: list, max_tokens: int = 800) -> str:
    """
    messages: list of {"role": "user"/"assistant", "content": str}
    Returns the assistant's reply text.
    """
    load_dotenv(override=True)

    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    # 1. Google Gemini
    if gemini_key and gemini_key.strip():
        # pyrefly: ignore [missing-import]
        from google import genai
        # pyrefly: ignore [missing-import]
        from google.genai import types

        client = genai.Client(api_key=gemini_key.strip())
        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=m["content"])]
                )
            )

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
        )

        max_retries = 3
        last_err = None
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=MODEL_GEMINI,
                    contents=contents,
                    config=config,
                )
                return response.text or ""
            except Exception as e:
                last_err = e
                err_msg = str(e)
                # Retry on 503 (high demand) or 429 (rate limit)
                if ("503" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg or "RESOURCE_EXHAUSTED" in err_msg) and attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise last_err

    # 2. OpenAI
    if openai_key and openai_key.strip():
        # pyrefly: ignore [missing-import]
        import openai
        client = openai.OpenAI(api_key=openai_key.strip())
        oai_messages = [{"role": "system", "content": system_prompt}] + messages
        res = client.chat.completions.create(
            model=MODEL_OPENAI,
            messages=oai_messages,
            max_tokens=max_tokens,
        )
        return res.choices[0].message.content or ""

    # 3. Anthropic
    if anthropic_key and anthropic_key.strip():
        # pyrefly: ignore [missing-import]
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key.strip())
        res = client.messages.create(
            model=MODEL_ANTHROPIC,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        return "".join(block.text for block in res.content if block.type == "text")

    raise ValueError(
        "No valid API key found. Please set GEMINI_API_KEY in backend/.env"
    )
