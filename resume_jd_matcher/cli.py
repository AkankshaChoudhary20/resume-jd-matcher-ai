"""
CLI entrypoint for resume-jd-matcher.

Usage:
    resume-jd-matcher --resume path/to/resume.txt --jd path/to/jd.txt
    python -m resume_jd_matcher.cli --resume path/to/resume.txt --jd path/to/jd.txt

Always prints the offline match analysis (score, matches, gaps). If
ANTHROPIC_API_KEY is set, additionally calls Claude for tailored resume
bullet suggestions; if not set, prints a clear message and skips that step
instead of crashing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from resume_jd_matcher import ai_suggest, matching


def _read_text_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if p.suffix.lower() != ".txt":
        print(
            f"Warning: '{path}' does not have a .txt extension. "
            "Only plain .txt input is supported (no PDF parsing) — "
            "attempting to read it as plain text anyway.",
            file=sys.stderr,
        )
    return p.read_text(encoding="utf-8", errors="replace")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resume-jd-matcher",
        description=(
            "Compare a resume against a job description: score skill/keyword "
            "overlap, identify gaps, and (optionally) generate AI-tailored "
            "resume bullet suggestions via the Claude API."
        ),
    )
    parser.add_argument(
        "--resume", required=True, help="Path to the resume .txt file."
    )
    parser.add_argument(
        "--jd", required=True, help="Path to the job description .txt file."
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Claude model to use for AI suggestions "
            f"(default: env ANTHROPIC_MODEL or '{ai_suggest.DEFAULT_MODEL}')."
        ),
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip AI suggestion generation even if an API key is available.",
    )
    return parser


def _print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def run(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        resume_text = _read_text_file(args.resume)
        jd_text = _read_text_file(args.jd)
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    result = matching.match(resume_text, jd_text)

    print("Resume / Job Description Match Analysis")
    print("=" * 41)
    print(f"Overall match score: {result.score:.1f} / 100")

    _print_section(f"Matched terms ({len(result.matches)})")
    if result.matches:
        for term in result.matches:
            print(f"  + {term}")
    else:
        print("  (none found)")

    _print_section(f"Gap terms — in JD but not in resume ({len(result.gaps)})")
    if result.gaps:
        for term in result.gaps:
            print(f"  - {term}")
    else:
        print("  (none found — great coverage!)")

    _print_section("AI-Generated Suggestions")
    if args.no_ai:
        print("Skipped (--no-ai flag set).")
    else:
        suggestion_result = ai_suggest.generate_suggestions(
            resume_text=resume_text,
            jd_text=jd_text,
            gaps=result.gaps,
            model=args.model,
        )
        if not suggestion_result.available:
            print(suggestion_result.message or "AI suggestions unavailable.")
        else:
            print(f"(model: {suggestion_result.model})")
            if suggestion_result.suggestions:
                for i, bullet in enumerate(suggestion_result.suggestions, 1):
                    print(f"  {i}. {bullet}")
            else:
                print("  (Claude returned no parseable suggestions)")

    print()
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
