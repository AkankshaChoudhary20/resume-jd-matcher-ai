import unittest
from resume_jd_matcher.matching import extract_terms

class UnicodePhraseSpacingTests(unittest.TestCase):
    def test_custom_product_phrase_normalizes_unicode_spaces(self):
        for separator in ('\u00a0', '\u2003', '\u202f', '\t', ' '):
            with self.subTest(separator=separator):
                self.assertIn('nebula forge', extract_terms('Nebula' + separator + 'Forge'))

    def test_product_phrases_do_not_cross_lines(self):
        for separator in ('\n', '\r\n', '\u2028', '\u2029'):
            self.assertNotIn('nebula forge', extract_terms('Nebula' + separator + 'Forge'))
