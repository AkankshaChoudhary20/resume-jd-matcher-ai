import pytest
from resume_jd_matcher.matching import extract_terms


@pytest.mark.parametrize('text', ['python_utils', 'my_python', 'pythoné', 'épython'])
def test_identifier_fragments_are_not_standalone_skills(text):
    assert 'python' not in extract_terms(text)


def test_punctuation_and_language_suffixes_still_match():
    assert {'python', 'c++', 'c#', '.net'} <= extract_terms('Python, C++; C# and .NET.')
