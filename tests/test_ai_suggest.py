"""
Unit tests for the Claude-backed suggestion module.

These tests NEVER make real network calls -- the anthropic client is
always mocked. They confirm:
  - the missing-API-key case degrades gracefully (no crash, clear message)
  - the prompt is built correctly from resume/jd/gaps
  - a mocked client response is parsed into suggestion bullets correctly
  - errors raised by the (mocked) client are handled gracefully
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import anthropic

from resume_jd_matcher import ai_suggest


class TestBuildPrompt:
    def test_prompt_includes_resume_jd_and_gaps(self):
        prompt = ai_suggest.build_prompt(
            resume_text="I know Python and Django.",
            jd_text="Looking for a Python and AWS engineer.",
            gaps=["aws", "kubernetes"],
        )
        assert "I know Python and Django." in prompt
        assert "Looking for a Python and AWS engineer." in prompt
        assert "aws" in prompt
        assert "kubernetes" in prompt
        assert "3 to 5" in prompt

    def test_prompt_handles_no_gaps(self):
        prompt = ai_suggest.build_prompt(
            resume_text="resume text", jd_text="jd text", gaps=[]
        )
        assert "no significant gaps found" in prompt


class TestMissingApiKey:
    def test_no_api_key_returns_unavailable_result(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = ai_suggest.generate_suggestions(
            resume_text="resume", jd_text="jd", gaps=["aws"]
        )
        assert result.available is False
        assert result.suggestions == []
        assert result.message == ai_suggest.NO_KEY_MESSAGE

    def test_no_api_key_does_not_raise(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        # Should not raise even though no client/network is available.
        result = ai_suggest.generate_suggestions("r", "j", [])
        assert isinstance(result, ai_suggest.SuggestionResult)


class TestGenerateSuggestionsWithMockedClient:
    def _make_mock_client(self, response_text: str):
        mock_client = MagicMock()
        text_block = SimpleNamespace(type="text", text=response_text)
        mock_response = SimpleNamespace(content=[text_block])
        mock_client.messages.create.return_value = mock_response
        return mock_client

    def test_parses_bullets_from_mocked_response(self):
        mock_client = self._make_mock_client(
            "- Led development of REST APIs using Python and Django.\n"
            "- Automated CI/CD pipeline reducing deploy time by 40%.\n"
            "- Collaborated cross-functionally with data science team.\n"
        )
        result = ai_suggest.generate_suggestions(
            resume_text="Python developer with Django experience.",
            jd_text="Looking for a Python engineer with AWS skills.",
            gaps=["aws"],
            api_key="fake-test-key",
            client=mock_client,
        )
        assert result.available is True
        assert len(result.suggestions) == 3
        assert "Led development of REST APIs using Python and Django." in result.suggestions

    def test_uses_default_model_when_not_specified(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
        mock_client = self._make_mock_client("- Bullet one.")
        result = ai_suggest.generate_suggestions(
            resume_text="r",
            jd_text="j",
            gaps=[],
            api_key="fake-test-key",
            client=mock_client,
        )
        assert result.model == ai_suggest.DEFAULT_MODEL
        called_kwargs = mock_client.messages.create.call_args.kwargs
        assert called_kwargs["model"] == ai_suggest.DEFAULT_MODEL

    def test_respects_explicit_model_override(self):
        mock_client = self._make_mock_client("- Bullet one.")
        result = ai_suggest.generate_suggestions(
            resume_text="r",
            jd_text="j",
            gaps=[],
            api_key="fake-test-key",
            model="claude-opus-5",
            client=mock_client,
        )
        assert result.model == "claude-opus-5"
        called_kwargs = mock_client.messages.create.call_args.kwargs
        assert called_kwargs["model"] == "claude-opus-5"

    def test_respects_model_env_var(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
        mock_client = self._make_mock_client("- Bullet one.")
        result = ai_suggest.generate_suggestions(
            resume_text="r",
            jd_text="j",
            gaps=[],
            api_key="fake-test-key",
            client=mock_client,
        )
        assert result.model == "claude-haiku-4-5"

    def test_prompt_sent_to_client_contains_resume_and_gaps(self):
        mock_client = self._make_mock_client("- Bullet one.")
        ai_suggest.generate_suggestions(
            resume_text="UNIQUE_RESUME_MARKER",
            jd_text="UNIQUE_JD_MARKER",
            gaps=["UNIQUE_GAP_MARKER"],
            api_key="fake-test-key",
            client=mock_client,
        )
        called_kwargs = mock_client.messages.create.call_args.kwargs
        sent_messages = called_kwargs["messages"]
        sent_content = sent_messages[0]["content"]
        assert "UNIQUE_RESUME_MARKER" in sent_content
        assert "UNIQUE_JD_MARKER" in sent_content
        assert "UNIQUE_GAP_MARKER" in sent_content

    def test_handles_api_error_gracefully(self):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.APIError(
            message="boom",
            request=MagicMock(),
            body=None,
        )
        result = ai_suggest.generate_suggestions(
            resume_text="r",
            jd_text="j",
            gaps=[],
            api_key="fake-test-key",
            client=mock_client,
        )
        assert result.available is False
        assert "AI suggestion request failed" in result.message
