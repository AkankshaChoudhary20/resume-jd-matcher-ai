import pytest
from resume_jd_matcher.matching import compute_similarity


@pytest.mark.parametrize('language',['C++','C#','C','R'])
def test_single_language_documents_have_full_similarity(language):
    assert compute_similarity(language,language)==100.0


@pytest.mark.parametrize('left,right',[('C++','C#'),('C','C++'),('C#','C')])
def test_distinct_languages_do_not_collapse_to_the_same_token(left,right):
    assert compute_similarity(left,right)==0.0


def test_language_names_remain_case_insensitive():
    assert compute_similarity('c++','C++')==100.0
