from resume_jd_matcher.matching import compute_similarity

def test_equivalent_unicode_compositions_have_identical_similarity():
    assert compute_similarity('café résumé', 'cafe\u0301 re\u0301sume\u0301') == 100.0
    assert compute_similarity('Python', 'Java') == 0.0
