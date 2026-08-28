import json
import logging
import os
from typing import Any

import requests
from flask import Flask, jsonify, render_template, request


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

DEFAULT_KIE_MODEL = "gpt-5.4-codex"
KIE_API_URL = os.getenv("KIE_API_URL", "https://api.kie.ai/api/v1/responses")
ALLOWED_MOODS = {
    "happy", "supportive", "calm", "curious", "playful",
    "surprised", "serious", "friendly",
}
MAX_HISTORY = 16
MAX_MESSAGE_LENGTH = 4000

SYSTEM_PROMPT = """You are A2 Friend, a friendly AI companion.

You can talk about almost any normal topic.
Always answer in simple CEFR A2 English.
Use short sentences, common words, and simple grammar.
Explain difficult ideas with easy examples.

Understand the user's emotion. Choose one mood: happy, supportive, calm,
curious, playful, surprised, serious, or friendly.
Be natural and friendly. Do not sound like a textbook.
If the user is sad, be supportive. If the user is happy, share their happiness.
If the user jokes, you can be playful. If the topic is serious, answer calmly.
Do not use too many emojis. Sometimes ask one simple follow-up question.
If the user writes in Russian or another language, understand it but normally
answer in simple English. Do not correct mistakes unless the user asks.
Most answers should contain 2-6 short sentences.

Return only valid JSON in this exact shape:
{"answer":"your answer here","mood":"friendly"}
Do not add markdown or text outside the JSON."""


def clean_history(value: Any) -> list[dict[str, str]]:
    """Keep only a small, safe slice of user/assistant conversation history."""
    if not isinstance(value, list):
        return []

    cleaned = []
    for item in value[-MAX_HISTORY:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and isinstance(content, str):
            content = content.strip()[:MAX_MESSAGE_LENGTH]
            if content:
                cleaned.append({"role": role, "content": content})
    return cleaned


def extract_text(api_data: Any) -> str:
    """Extract output_text from Kie AI's Responses API message output."""
    if not isinstance(api_data, dict):
        raise ValueError("Kie AI returned a non-object response")

    output = api_data.get("output", [])
    if not isinstance(output, list):
        raise ValueError("Could not find model text in Kie AI response")

    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue

        content = item.get("content", [])
        if not isinstance(content, list):
            continue

        for part in content:
            if (
                isinstance(part, dict)
                and part.get("type") == "output_text"
                and isinstance(part.get("text"), str)
            ):
                return part["text"]

    raise ValueError("Could not find model text in Kie AI response")


def build_input_text(history: list[dict[str, str]], message: str) -> str:
    """Combine instructions and conversation into one Responses API input."""
    conversation = []
    for item in history:
        label = "User" if item["role"] == "user" else "A2 Friend"
        conversation.append(f"{label}: {item['content']}")
    conversation_text = "\n".join(conversation) or "No earlier messages."

    return (
        f"{SYSTEM_PROMPT}\n\n"
        "Recent conversation:\n"
        f"{conversation_text}\n\n"
        "New message:\n"
        f"User: {message}\n\n"
        "Reply to the new message now. Return only the required JSON."
    )


def parse_model_reply(raw_text: str) -> tuple[str, str]:
    """Turn the model's JSON text into a safe answer and known mood."""
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Model did not return JSON")
        result = json.loads(text[start:end + 1])

    answer = result.get("answer") if isinstance(result, dict) else None
    mood = result.get("mood", "friendly") if isinstance(result, dict) else "friendly"
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Model response has no answer")
    mood = mood.lower().strip() if isinstance(mood, str) else "friendly"
    return answer.strip()[:6000], mood if mood in ALLOWED_MOODS else "friendly"


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/chat")
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Please send a valid message."), 400

    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        return jsonify(error="Please write a message first."), 400
    message = message.strip()
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify(error="Your message is too long. Please make it shorter."), 400

    api_key = os.getenv("KIE_API_KEY")
    if not api_key:
        app.logger.error("KIE_API_KEY is not set")
        return jsonify(error="A2 Friend cannot answer right now. Please try again."), 503

    history = clean_history(data.get("history"))
    # The current message is sent separately, so avoid duplicating it.
    if history and history[-1] == {"role": "user", "content": message}:
        history.pop()

    payload = {
        "model": os.getenv("KIE_MODEL", DEFAULT_KIE_MODEL),
        "stream": False,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": build_input_text(history, message),
                    }
                ],
            }
        ],
        "reasoning": {"effort": "low"},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.post(KIE_API_URL, headers=headers, json=payload, timeout=45)
        if response.status_code != 200:
            app.logger.error(
                "Kie AI error %s: %s",
                response.status_code,
                response.text,
            )
            return jsonify(
                error="A2 Friend cannot answer right now. Please try again."
            ), 502

        result = response.json()
        app.logger.info(
            "Kie AI response keys: %s",
            list(result.keys()) if isinstance(result, dict) else type(result),
        )
        try:
            model_text = extract_text(result)
        except ValueError:
            app.logger.error(
                "Kie AI response did not contain output_text: %s",
                response.text[:3000],
            )
            raise

        answer, mood = parse_model_reply(model_text)
        return jsonify(answer=answer, mood=mood)
    except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
        app.logger.exception("Kie AI request failed: %s", exc)
        return jsonify(error="A2 Friend cannot answer right now. Please try again."), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3000")))
