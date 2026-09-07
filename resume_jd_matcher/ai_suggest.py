"""
Claude-backed suggestion generation.

Given a resume, a job description, and the gap terms computed by
resume_jd_matcher.matching (JD terms missing from the resume), this module
asks Claude for 3-5 tailored resume bullet points that honestly reflect
experience implied by the resume while addressing the JD's gaps.

Design constraints:
  - Reads the API key ONLY from the ANTHROPIC_API_KEY environment variable
    (unless a key is explicitly passed in for testing/override).
  - If no API key is available, `generate_suggestions` returns a clear,
    non-crashing result explaining that AI suggestions are being skipped --
    it never raises for the missing-key case.
  - The model name is configurable via the ANTHROPIC_MODEL env var or the
    `model=` argument, defaulting to `claude-sonnet-5`.
  - The prompt explicitly instructs Claude not to fabricate credentials,
    only to rephrase/emphasize real experience toward the JD's language.
  - Network calls only happen inside generate_suggestions() (and only when
    a key is present) -- this keeps resume_jd_matcher.matching fully
    network-free and independently testable.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import anthropic

DEFAULT_MODEL = "claude-sonnet-5"
NO_KEY_MESSAGE = "No API key set — skipping AI suggestions, showing match analysis only."

SYSTEM_PROMPT = (
    "You are a careful, honest resume-writing assistant. You help candidates "
    "tailor resume bullet points to a specific job description. You NEVER "
    "invent credentials, employers, job titles, tools, certifications, or "
    "achievements the candidate did not mention. You only rephrase, "
    "reframe, or emphasize experience that is already present in the "
    "candidate's resume, using language and terminology closer to the job "
    "description. If the resume genuinely lacks a skill, you may suggest "
    "how the candidate could phrase adjacent/transferable experience "
    "honestly, but you must not claim they have it."
)


def get_api_key() -> str | None:
    """Read the Anthropic API key from the environment."""
    return os.environ.get("ANTHROPIC_API_KEY")


def get_default_model() -> str:
    """Resolve the default model, allowing override via ANTHROPIC_MODEL."""
    return os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)


def build_prompt(resume_text: str, jd_text: str, gaps: list[str]) -> str:
    """
    Build the user-turn prompt sent to Claude. Pure string formatting, no
    network call -- kept as its own function so it's directly unit
    testable.
    """
    gaps_block = "\n".join(f"- {g}" for g in gaps) if gaps else "(no significant gaps found)"

    return (
        "Here is a candidate's resume:\n"
        "-----RESUME-----\n"
        f"{resume_text.strip()}\n"
        "-----END RESUME-----\n\n"
        "Here is the target job description:\n"
        "-----JOB DESCRIPTION-----\n"
        f"{jd_text.strip()}\n"
        "-----END JOB DESCRIPTION-----\n\n"
        "The following key terms/skills appear in the job description but "
        "were not detected in the resume (gap terms):\n"
        f"{gaps_block}\n\n"
        "Task: Suggest 3 to 5 tailored resume bullet points the candidate "
        "could add or use to revise their resume for this job. Each bullet "
        "should:\n"
        "  1. Be grounded in experience actually implied by the resume "
        "(do not fabricate employers, titles, tools, or accomplishments).\n"
        "  2. Where honestly possible, use terminology from the job "
        "description / gap terms above to better match the JD's language.\n"
        "  3. Be concise, specific, and results-oriented (like a real "
        "resume bullet).\n\n"
        "Return ONLY the bullet points, one per line, each starting with "
        "'- '. Do not include any other commentary."
    )


def _parse_bullets(text: str) -> list[str]:
    """Parse bullet points out of Claude's response text."""
    bullets = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip common bullet/number prefixes: "- ", "* ", "1. ", "1) "
        cleaned = re.sub(r"^[-*•]\s+", "", line)
        cleaned = re.sub(r"^\d+[.)]\s+", "", cleaned)
        cleaned = cleaned.strip()
        if cleaned:
            bullets.append(cleaned)
    return bullets


@dataclass
class SuggestionResult:
    available: bool
    suggestions: list[str] = field(default_factory=list)
    message: str | None = None
    model: str | None = None
    raw_text: str | None = None

    def to_dict(self) -> dict:
        return {
            "available": self.available,
            "suggestions": self.suggestions,
            "message": self.message,
            "model": self.model,
            "raw_text": self.raw_text,
        }


def generate_suggestions(
    resume_text: str,
    jd_text: str,
    gaps: list[str],
    api_key: str | None = None,
    model: str | None = None,
    client: "anthropic.Anthropic | None" = None,
    max_tokens: int = 1024,
) -> SuggestionResult:
    """
    Generate tailored resume bullet suggestions via the Claude API.

    Gracefully degrades (does NOT raise) when no API key is available:
    returns a SuggestionResult with available=False and an explanatory
    message.

    `client` may be injected (e.g. a mock) for testing -- if omitted, a
    real anthropic.Anthropic client is constructed using the resolved API
    key.
    """
    resolved_key = api_key or get_api_key()

    if not resolved_key:
        return SuggestionResult(available=False, message=NO_KEY_MESSAGE)

    resolved_model = model or get_default_model()
    prompt = build_prompt(resume_text, jd_text, gaps)

    if client is None:
        client = anthropic.Anthropic(api_key=resolved_key)

    try:
        response = client.messages.create(
            model=resolved_model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        return SuggestionResult(
            available=False,
            message=f"AI suggestion request failed: {e}",
            model=resolved_model,
        )

    text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    suggestions = _parse_bullets(text)

    return SuggestionResult(
        available=True,
        suggestions=suggestions,
        message=None,
        model=resolved_model,
        raw_text=text,
    )
