import unittest
from resume_jd_matcher.matching import extract_terms

class LanguageBoundaryTests(unittest.TestCase):
    def test_extended_language_names_do_not_match_prefix(self):
        self.assertNotIn('c++', extract_terms('C+++'))
        self.assertNotIn('c#', extract_terms('C##'))
        self.assertNotIn('c++', extract_terms('XC++'))

    def test_valid_language_names_and_punctuation_match(self):
        self.assertIn('c++', extract_terms('(C++), C#;'))
        self.assertIn('c#', extract_terms('(C++), C#;'))
