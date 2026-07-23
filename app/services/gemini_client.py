from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class GeminiAPIError(Exception):
    """Raised when the Gemini API request fails."""


MODEL_NAME = "gemini-3.5-flash-lite"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"
TIMEOUT_SECONDS = 15.0


def _get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiAPIError("GEMINI_API_KEY is not set")
    return api_key


def _extract_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    if not candidates:
        raise GeminiAPIError("Gemini returned no candidates; the request may have been blocked by safety settings")

    candidate = candidates[0]
    content = candidate.get("content") or {}
    parts = content.get("parts") or []
    if not parts:
        raise GeminiAPIError("Gemini returned no content parts")

    text = parts[0].get("text")
    if not text:
        raise GeminiAPIError("Gemini returned an empty response")
    return text


async def _post_prompt(prompt: str) -> str:
    api_key = _get_api_key()
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}],
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)
    except httpx.TimeoutException as exc:
        raise GeminiAPIError("Gemini API request timed out") from exc

    if response.status_code != 200:
        message = response.text or "Gemini API request failed"
        raise GeminiAPIError(f"Gemini API request failed with status {response.status_code}: {message}")

    try:
        response_payload = response.json()
    except ValueError as exc:
        raise GeminiAPIError("Gemini API returned an invalid JSON response") from exc

    return _extract_text(response_payload)


async def analyze_workout(workout_summary: str) -> str:
    prompt = (
        "You are a fitness coach. Analyze this workout and give brief, actionable feedback "
        "(form tips, intensity assessment, and one suggestion for the next session). "
        "Keep it under 150 words.\n\nWorkout details:\n"
        f"{workout_summary}"
    )
    return await _post_prompt(prompt)


async def generate_weekly_plan(recent_workouts_summary: str, user_goal: str | None) -> str:
    goal_text = f" Consider the user's goal: {user_goal}." if user_goal else ""
    prompt = (
        "Create a balanced 7-day training plan across gym, run, and swim activities based on the recent "
        "workout history. Include a mix of recovery, endurance, and strength work, and keep the plan practical "
        f"for a real-world week.{goal_text}\n\nRecent workout history:\n{recent_workouts_summary}"
    )
    return await _post_prompt(prompt)
