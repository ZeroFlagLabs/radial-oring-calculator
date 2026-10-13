"""Ensure shortening visible decimal places never disguises critical tolerances."""
import unittest
from src.ui.precision import format_input

class InputPrecisionTests(unittest.TestCase):
    def test_three_places_for_simple_dimensions(self):
        self.assertEqual(format_input(.103),"0.103")
        self.assertEqual(format_input(.070),"0.070")
    def test_four_places_when_requested(self):
        self.assertEqual(format_input(.103,4),"0.1030")
        self.assertEqual(format_input(.1425,4),"0.1425")
    def test_auto_maintain_extra_significant_precision(self):
        self.assertEqual(format_input(.0835),"0.0835")
        self.assertEqual(format_input(.0005),"0.0005")
        self.assertEqual(format_input(.00025),"0.00025")
        self.assertEqual(format_input(.00025,4),"0.00025")
    def test_zero(self):
        self.assertEqual(format_input(0),"0.000")
    def test_invalid_precision(self):
        with self.assertRaises(ValueError): format_input(.1,2)

if __name__ == "__main__":
    unittest.main()

class ResultFormattingTests(unittest.TestCase):
    def test_results_presentation(self):
        from src.ui.precision import format_result
        self.assertEqual(format_result(17.394,'percent'),'17.39')
        self.assertEqual(format_result(0.00025,'dimension'),'0.00025')
        self.assertEqual(format_result(.045019,'area'),'0.045019')
        self.assertEqual(format_result(.000123,'percent'),'0.000123')
    def test_angle_display(self):
        self.assertEqual(format_input(24,1),'24.0')
