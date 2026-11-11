from resume_jd_matcher.matching import compute_similarity, extract_terms

def test_fullwidth_skills_match_plain_text():
    assert "python" in extract_terms("Ｐｙｔｈｏｎ")
    assert compute_similarity("Ｐｙｔｈｏｎ ＳＱＬ", "Python SQL") == 100.0

def test_compatibility_normalization_preserves_language_punctuation():
    assert compute_similarity("Ｃ＋＋", "C++") == 100.0
    assert compute_similarity("Ｃ＃", "C++") == 0.0
