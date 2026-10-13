"""Catalogue identification is passive and checks ALL four entered dimensions."""
import unittest
from src.catalog.as568 import load_as568
from src.catalog.matching import matching_sizes


class ManualSizeMatchingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sizes = load_as568()

    def test_exact_as568_112(self):
        matches = matching_sizes(self.sizes, .487,.005,.103,.003)
        self.assertEqual([m.dash for m in matches],['-112'])

    def test_wrong_id_tolerance_no_match(self):
        self.assertEqual(matching_sizes(self.sizes,.487,.009,.103,.003),())

    def test_wrong_section_tolerance_no_match(self):
        self.assertEqual(matching_sizes(self.sizes,.487,.005,.103,.004),())

    def test_inexact_nominal_no_match(self):
        self.assertEqual(matching_sizes(self.sizes,.487001,.005,.103,.003),())

    def test_no_match(self):
        self.assertEqual(matching_sizes(self.sizes,.494,.001,.103,.001),())

    def test_actual_values_not_nominal_fractions(self):
        self.assertEqual([m.dash for m in matching_sizes(self.sizes,.029,.004,.040,.003)],['-001'])
        self.assertEqual(matching_sizes(self.sizes,.070,.004,.040,.003),())


if __name__=='__main__':
    unittest.main()
