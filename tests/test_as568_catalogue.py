"""Reference catalogue transcription sanity checks (not AS568 revision certification)."""
import unittest
from collections import Counter
from src.catalog.as568 import load_as568

class AS568CatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sizes = load_as568()
        cls.index = {x.dash:x for x in cls.sizes}

    def test_counts_and_unique_keys(self):
        self.assertEqual(len(self.sizes), 349)
        self.assertEqual(len(self.index),349)
        self.assertNotIn("-101", self.index)
        self.assertNotIn("-900", self.index)
        self.assertNotIn("-901", self.index)
        self.assertNotIn("-001 1/2",self.index)

    def test_p_f_verified_tolerance_corrections(self):
        self.assertEqual(self.index["-469"].id_tol_in, .095)
        self.assertEqual(self.index["-470"].id_tol_in, .095)

    def test_cross_sections(self):
        counts=Counter(s.cs_in for s in self.sizes)
        self.assertEqual(set(counts), {.040,.050,.060,.070,.103,.139,.210,.275})

    def test_example_112(self):
        s=self.index["-112"]
        self.assertEqual((s.id_in,s.id_tol_in,s.cs_in,s.cs_tol_in),(.487,.005,.103,.003))

    def test_large_sizes(self):
        s=self.index["-475"]
        self.assertEqual((s.id_in,s.id_tol_in,s.cs_in,s.cs_tol_in),(25.940,.120,.275,.006))
        s=self.index["-380"]
        self.assertEqual((s.id_in,s.id_tol_in,s.cs_in,s.cs_tol_in),(11.475,.065,.210,.005))

if __name__ == "__main__":
    unittest.main()
