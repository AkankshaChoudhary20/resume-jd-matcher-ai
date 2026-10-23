import unittest

from resume_jd_matcher.matching import compute_similarity


class DottedTechnologyTests(unittest.TestCase):
    def test_dotted_technology_names_are_distinct_tokens(self):
        for technology, different in [
            ('.NET', 'net'), ('ASP.NET', 'ASP'), ('Node.js', 'node'),
            ('React.js', 'React'), ('Vue.js', 'js')
        ]:
            with self.subTest(technology=technology):
                self.assertEqual(compute_similarity(technology, different), 0.0)
                self.assertEqual(compute_similarity(technology, technology.lower()), 100.0)

    def test_sentence_punctuation_does_not_change_tokens(self):
        self.assertEqual(compute_similarity('Node.js, ASP.NET.', 'node.js asp.net'), 100.0)

    def test_language_suffixes_remain_distinct(self):
        self.assertEqual(compute_similarity('C++', 'C#'), 0.0)
        self.assertEqual(compute_similarity('R', 'R'), 100.0)
