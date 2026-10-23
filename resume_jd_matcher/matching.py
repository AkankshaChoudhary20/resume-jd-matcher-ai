"""
Core matching logic: resume vs. job description.

Pure functions only -- NO network calls anywhere in this module. Safe to
unit test in isolation and safe to run with zero API keys / zero network
access.

Approach (kept intentionally simple and explainable -- see README for more):

1. Overall similarity score (0-100):
   TF-IDF vectorize the resume and JD text, then compute the cosine
   similarity between the two vectors and scale it to a 0-100 score.

2. Term/skill extraction ("gaps" and "matches"):
   Candidate terms are pulled from each document using two simple,
   explainable techniques:
     a) Known-skills lookup: a curated, extendable list of common tech /
        professional skill keywords (resume_jd_matcher/skills_data.py) is
        matched against the text (case-insensitive, word-boundary aware,
        multi-word phrases supported).
     b) Capitalized multi-word phrase extraction: sequences of two or more
        Title-Case / ALLCAPS words (e.g. "Google Cloud Platform", "REST
        API") are extracted as candidate proper-noun / product / tool
        terms, since these are frequently skills, tools, or technologies
        not present in the curated list.
   Terms found in the JD's candidate set but not in the resume's candidate
   set are "gaps". Terms found in both are "matches".

This is deliberately not a full NLP pipeline (no POS tagging, no NER
model) -- it's a fast, dependency-light heuristic that works well for
typical resume/JD text and is easy to extend (just add to
skills_data.KNOWN_SKILLS).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from resume_jd_matcher.skills_data import KNOWN_SKILLS

# Precompute a regex-friendly, longest-first sorted list so that multi-word
# skills are matched before their shorter substrings (e.g. "machine
# learning" before "learning" -- though "learning" alone isn't in the list,
# this ordering matters in general for future additions).
_SORTED_SKILLS = sorted(set(s.lower() for s in KNOWN_SKILLS), key=len, reverse=True)

# Matches 2-5 capitalized/ALLCAPS words in a row, e.g. "Google Cloud
# Platform", "REST API", "Amazon Web Services". Each word must start with
# an uppercase letter (or be all-caps, incl. acronyms with digits like
# "S3" or "OAuth2" won't fully match here but simple acronyms like "AWS"
# will via KNOWN_SKILLS / this regex as a single-cap-word fallback below).
# The separator is restricted to spaces/tabs (NOT newlines) and the chain
# is capped at 5 words so section headers / running prose don't get
# swallowed into one giant multi-line "phrase".
_CAP_PHRASE_RE = re.compile(
    r"\b([A-Z][a-zA-Z0-9+.#]*(?:[ \t]+[A-Z][a-zA-Z0-9+.#]*){1,4})\b"
)

_WORD_RE = re.compile(r"[a-zA-Z0-9+#.]+")


def _normalize(text: str) -> str:
    return text.lower().strip()


def _skill_regex(skill: str) -> re.Pattern:
    """Build a word-boundary regex for a (possibly multi-word) skill.

    Allows an optional trailing "s" so simple plurals (e.g. "REST APIs"
    matching the skill "rest api") are still recognized.
    """
    escaped = re.escape(skill)
    # Allow the internal whitespace to match one-or-more whitespace chars.
    escaped = escaped.replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-zA-Z0-9+#]){escaped}s?(?![a-zA-Z0-9+#])")


_SKILL_PATTERNS = {skill: _skill_regex(skill) for skill in _SORTED_SKILLS}


def extract_terms(text: str) -> set[str]:
    """
    Extract a set of candidate skill/keyword terms from free text.

    Combines:
      1. Curated known-skills lookup (case-insensitive, word-boundary safe).
      2. Capitalized multi-word phrase extraction (candidate proper nouns /
         tools / technologies not in the curated list).

    Returns a set of normalized (lowercased) term strings.
    """
    if not text:
        return set()

    normalized = _normalize(text)
    found: set[str] = set()

    # 1. Known skills lookup.
    for skill, pattern in _SKILL_PATTERNS.items():
        if pattern.search(normalized):
            found.add(skill)

    # 2. Capitalized multi-word phrase extraction (run on the ORIGINAL text,
    #    line by line, since case matters here and phrases should never
    #    span a line break).
    for line in text.splitlines():
        for m in _CAP_PHRASE_RE.finditer(line):
            phrase = m.group(1).strip()
            # Strip trailing punctuation (e.g. "TypeScript." at end of a
            # sentence, or "Django," mid-sentence).
            phrase = phrase.rstrip(".,;:!?")
            words = phrase.split()
            # Filter out phrases that are just the start of a sentence (a
            # single capitalized word) by requiring at least 2 words and a
            # minimum length.
            if len(words) < 2:
                continue
            if len(phrase) < 5:
                continue
            found.add(" ".join(phrase.lower().split()))

    return found


def compute_similarity(resume_text: str, jd_text: str) -> float:
    """
    Compute an overall similarity score (0-100) between resume_text and
    jd_text using TF-IDF vectorization + cosine similarity.

    Returns 0.0 if either text is empty/whitespace-only.
    """
    if not resume_text or not resume_text.strip():
        return 0.0
    if not jd_text or not jd_text.strip():
        return 0.0

    # Preserve C++, C#, single-letter skills, and dotted names such as
    # Node.js, ASP.NET and .NET as distinct technology tokens.
    vectorizer = TfidfVectorizer(stop_words="english", token_pattern=r"(?u)(?<![\w.])(?:\.\w+|\w+(?:\.\w+)*)(?:\+\+|#)?")
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
    except ValueError:
        # Happens if, after removing stopwords, there's no vocabulary left
        # (e.g. both docs are only stopwords/punctuation).
        return 0.0

    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    score = round(float(similarity) * 100, 2)
    return max(0.0, min(100.0, score))


@dataclass
class MatchResult:
    score: float
    matches: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    resume_terms: list[str] = field(default_factory=list)
    jd_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "matches": self.matches,
            "gaps": self.gaps,
            "resume_terms": self.resume_terms,
            "jd_terms": self.jd_terms,
        }


def match(resume_text: str, jd_text: str) -> MatchResult:
    """
    Compare resume_text against jd_text.

    Returns a MatchResult with:
      - score: overall similarity, 0-100 (TF-IDF cosine similarity).
      - matches: sorted list of terms present in BOTH the JD and resume.
      - gaps: sorted list of terms present in the JD but NOT in the resume
        (candidate skills/keywords to address).
      - resume_terms / jd_terms: the full extracted term sets, for
        reference/debugging.
    """
    score = compute_similarity(resume_text, jd_text)

    resume_terms = extract_terms(resume_text)
    jd_terms = extract_terms(jd_text)

    matches = sorted(resume_terms & jd_terms)
    gaps = sorted(jd_terms - resume_terms)

    return MatchResult(
        score=score,
        matches=matches,
        gaps=gaps,
        resume_terms=sorted(resume_terms),
        jd_terms=sorted(jd_terms),
    )

