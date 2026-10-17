import unittest
from resume_jd_matcher.matching import extract_terms,match
class PhraseWhitespaceTests(unittest.TestCase):
    def test_phrase_whitespace_does_not_create_false_gaps(self):
        self.assertIn('quantum widget platform',extract_terms('Quantum\tWidget   Platform'))
        result=match('Quantum\tWidget   Platform','Quantum Widget Platform')
        self.assertIn('quantum widget platform',result.matches)
        self.assertNotIn('quantum widget platform',result.gaps)
    def test_phrases_still_do_not_cross_lines(self):
        self.assertNotIn('quantum widget platform',extract_terms('Quantum\nWidget Platform'))
