"""
Unit tests for the core, network-free matching module.
"""

from resume_jd_matcher import matching


class TestComputeSimilarity:
    def test_identical_text_scores_high(self):
        text = (
            "Experienced Python developer with strong Django and PostgreSQL "
            "background, skilled in REST API design and Docker deployment."
        )
        score = matching.compute_similarity(text, text)
        assert score >= 95.0

    def test_unrelated_text_scores_low(self):
        resume = (
            "Professional chef with 10 years of experience in fine dining "
            "restaurants, specializing in French pastry and menu design."
        )
        jd = (
            "Seeking a nuclear physicist with expertise in particle "
            "accelerators, quantum field theory, and radiation safety "
            "protocols for a national laboratory."
        )
        score = matching.compute_similarity(resume, jd)
        assert score < 20.0

    def test_partial_overlap_scores_in_between(self):
        resume = "Software engineer skilled in Python, Django, and PostgreSQL."
        jd = "Looking for a software engineer with Python and AWS experience."
        score = matching.compute_similarity(resume, jd)
        assert 0.0 < score < 100.0

    def test_empty_resume_returns_zero(self):
        assert matching.compute_similarity("", "Some job description text") == 0.0
        assert matching.compute_similarity("   ", "Some job description text") == 0.0

    def test_empty_jd_returns_zero(self):
        assert matching.compute_similarity("Some resume text", "") == 0.0

    def test_score_in_valid_range(self):
        resume = "Data scientist with Python, pandas, and scikit-learn experience."
        jd = "Hiring a data scientist skilled in machine learning and Python."
        score = matching.compute_similarity(resume, jd)
        assert 0.0 <= score <= 100.0


class TestExtractTerms:
    def test_known_skill_extraction_case_insensitive(self):
        text = "I have experience with PYTHON, Django, and postgresql."
        terms = matching.extract_terms(text)
        assert "python" in terms
        assert "django" in terms
        assert "postgresql" in terms

    def test_multiword_known_skill_extraction(self):
        text = "Experienced with machine learning and Amazon Web Services."
        terms = matching.extract_terms(text)
        assert "machine learning" in terms
        assert "amazon web services" in terms

    def test_word_boundary_no_false_positive_substring(self):
        # "java" should NOT match inside "javascript" as a standalone term,
        # but "javascript" itself should be found.
        text = "Experienced JavaScript developer."
        terms = matching.extract_terms(text)
        assert "javascript" in terms
        assert "java" not in terms

    def test_capitalized_phrase_extraction(self):
        text = "Built internal tools using Google Cloud Platform and Jenkins Pipelines."
        terms = matching.extract_terms(text)
        assert "google cloud platform" in terms

    def test_empty_text_returns_empty_set(self):
        assert matching.extract_terms("") == set()
        assert matching.extract_terms(None) == set()


class TestMatch:
    def test_gap_and_match_terms_on_crafted_example(self):
        resume = (
            "Software Engineer experienced in Python, Django, PostgreSQL, "
            "Git, and Docker. Built REST APIs and wrote unit tests."
        )
        jd = (
            "Looking for a Software Engineer with Python, Django, and AWS "
            "experience. Kubernetes and Terraform knowledge is a plus. "
            "Must be comfortable with REST APIs and unit testing."
        )
        result = matching.match(resume, jd)

        # Terms present in both.
        assert "python" in result.matches
        assert "django" in result.matches
        assert "rest api" in result.matches or "rest apis" in " ".join(result.matches)

        # Terms in JD but missing from resume.
        assert "aws" in result.gaps
        assert "kubernetes" in result.gaps
        assert "terraform" in result.gaps

        # Gap terms should never also be match terms.
        assert set(result.gaps).isdisjoint(set(result.matches))

        # Score should be a sane float in range.
        assert 0.0 <= result.score <= 100.0

    def test_match_result_to_dict(self):
        result = matching.match("Python developer.", "Python developer needed.")
        d = result.to_dict()
        assert "score" in d
        assert "matches" in d
        assert "gaps" in d
        assert "resume_terms" in d
        assert "jd_terms" in d

    def test_no_gaps_when_resume_covers_everything(self):
        text = "Python, Django, PostgreSQL, Docker, Git, REST API."
        result = matching.match(text, text)
        assert result.gaps == []
