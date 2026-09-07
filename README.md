# resume-jd-matcher

A CLI/library tool that compares a resume against a job description (JD),
scores skill/keyword overlap, identifies gaps, and — if an
`ANTHROPIC_API_KEY` is available — uses the Claude API to generate tailored,
honest resume bullet point suggestions addressing those gaps.

The core matching logic works **fully offline**, with no API key and no
network access required. The Claude-backed suggestion step is optional and
degrades gracefully when no key is set.

## Features

- **Offline match analysis** (`resume_jd_matcher/matching.py`, pure
  functions, no network calls):
  - Overall similarity score (0-100) via TF-IDF + cosine similarity.
  - "Matches" — key terms/skills found in both the resume and the JD.
  - "Gaps" — key terms/skills found in the JD but missing from the resume.
- **AI-tailored suggestions** (`resume_jd_matcher/ai_suggest.py`, optional):
  calls the Claude API to draft 3-5 resume bullet points that honestly
  reflect experience implied by the resume, phrased toward the JD's
  language and gap terms. The prompt explicitly instructs Claude not to
  fabricate credentials/experience.
- **CLI** (`resume-jd-matcher`): reads plain `.txt` resume/JD files and
  prints the full analysis, plus AI suggestions when available.

## Setup

```bash
git clone <this-repo>
cd resume-jd-matcher-ai
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

(Optional) install the package itself so the `resume-jd-matcher` console
command is available:

```bash
pip install -e .
```

## Usage

```bash
# Using the installed console script:
resume-jd-matcher --resume sample_data/resume_example.txt --jd sample_data/jd_example.txt

# Or without installing, via the module:
python -m resume_jd_matcher.cli --resume sample_data/resume_example.txt --jd sample_data/jd_example.txt
```

This prints:

1. The overall match score (0-100).
2. Matched terms (present in both resume and JD).
3. Gap terms (present in JD, missing from resume).
4. AI-generated suggested resume bullets — **only if** `ANTHROPIC_API_KEY`
   is set in the environment. If it's not set, the CLI prints:

   ```
   No API key set — skipping AI suggestions, showing match analysis only.
   ```

   instead of crashing.

### Enabling AI suggestions

```bash
export ANTHROPIC_API_KEY=sk-ant-...
resume-jd-matcher --resume sample_data/resume_example.txt --jd sample_data/jd_example.txt
```

### Configuring the model

The Claude model used for suggestions defaults to `claude-sonnet-5`. Override
it via:

```bash
# environment variable
export ANTHROPIC_MODEL=claude-opus-5

# or CLI flag (takes precedence over the env var)
resume-jd-matcher --resume r.txt --jd j.txt --model claude-opus-5
```

Skip the AI step entirely (even if a key is set) with `--no-ai`.

### Input format

Only plain `.txt` files are supported. **PDF parsing is explicitly out of
scope** — convert your resume/JD to plain text first (e.g. `pdftotext`, or
copy-paste into a `.txt` file).

## How the matching algorithm works

1. **Similarity score**: both documents are vectorized with scikit-learn's
   `TfidfVectorizer` (English stop words removed), and the cosine
   similarity between the two TF-IDF vectors is computed and scaled to
   0-100. This captures overall textual/topical similarity, not just
   keyword overlap.

2. **Term/skill extraction** (used for matches/gaps), combining two simple,
   explainable techniques:
   - **Known-skills lookup**: a curated, extendable list of ~150 common
     tech/professional skill keywords
     (`resume_jd_matcher/skills_data.py`), matched case-insensitively with
     word-boundary awareness (so "java" doesn't match inside
     "javascript"), including simple plural handling ("REST APIs" matches
     the skill "rest api").
   - **Capitalized multi-word phrase extraction**: sequences of 2-5
     Title-Case/ALLCAPS words on the same line (e.g. "Google Cloud
     Platform") are extracted as candidate proper-noun/tool/technology
     terms not covered by the curated list.

   Terms found in the JD's extracted set but not the resume's are "gaps";
   terms in both are "matches".

3. **AI suggestions**: the resume, JD, and computed gap terms are sent to
   Claude with an explicit instruction to suggest 3-5 bullet points that
   are grounded in real experience already implied by the resume (no
   fabricated employers, titles, tools, or achievements) but phrased
   using the JD's terminology where honestly applicable.

### Limitations

- This is a lightweight heuristic, not a full NLP pipeline — there's no
  POS tagging, named-entity recognition, or semantic understanding beyond
  TF-IDF term-frequency weighting.
- The known-skills list is a starting point, not exhaustive. Extend
  `resume_jd_matcher/skills_data.py` with domain-specific terms (e.g.
  legal, healthcare, marketing) as needed.
- Capitalized-phrase extraction will occasionally pick up section headers
  or company names (e.g. "About The Role") rather than true skills —
  treat gap terms as a starting point for review, not ground truth.
- The TF-IDF similarity score reflects lexical/topical overlap, not a
  judgment of candidate fit or qualification.
- No PDF/DOCX parsing — plain `.txt` input only.
- AI suggestions are only as good as the resume/JD text provided, and are
  explicitly instructed not to invent experience — but you should always
  review AI-generated text before using it.

## Running tests

```bash
source venv/bin/activate
pytest
```

All tests are network-free. The `ai_suggest` tests mock the `anthropic`
client — no real API calls are made during testing, and no API key is
required to run the test suite.

## Project structure

```
resume_jd_matcher/
  __init__.py
  matching.py       # Core matching logic (pure functions, no network calls)
  ai_suggest.py      # Claude-backed suggestion generation (optional, network)
  skills_data.py     # Curated/extendable known-skills keyword list
  cli.py              # CLI entrypoint
tests/
  test_matching.py    # Unit tests for core matching (no network)
  test_ai_suggest.py  # Unit tests for AI suggestions (mocked client, no network)
sample_data/
  resume_example.txt
  jd_example.txt
requirements.txt
setup.py
```

## License

Provided as-is for personal/demo use.
