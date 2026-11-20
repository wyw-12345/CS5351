"""T1: REQ-FUNC-001, REQ-INV-001, REQ-SEC-007."""

import copy
import tempfile
import unittest
from decimal import getcontext, localcontext
from pathlib import Path

from src.contracts import ValidationError, parse_json, read_text, validate_essay, validate_rubric
from src.score_calculator import calculate_score
from test.support import RUBRIC, SCORES


class CalculatorTests(unittest.TestCase):
    def test_weighted_result_and_bounds(self):
        """REQ-FUNC-004: weighted result and bounds."""
        self.assertEqual(calculate_score(RUBRIC, SCORES), "72.00")
        self.assertEqual(calculate_score(RUBRIC, {"content": "0", "structure": "0"}), "0.00")
        self.assertEqual(calculate_score(RUBRIC, {"content": "10", "structure": "10"}), "100.00")

    def test_different_maxima_rounding_and_external_context(self):
        """REQ-FUNC-004: different maxima rounding and external context."""
        rubric = {"id": "rounding", "version": "1", "criteria": [
            {"id": "x", "description": "x", "max_score": "8", "weight": "1"}]}
        with localcontext():
            getcontext().prec = 2
            self.assertEqual(calculate_score(rubric, {"x": "1.234"}), "15.43")
        rubric = copy.deepcopy(RUBRIC)
        rubric["criteria"][1]["max_score"] = "20"
        self.assertEqual(calculate_score(rubric, {"content": "8", "structure": "12"}), "72.00")

    def test_invalid_scores_rejected(self):
        """REQ-INV-004: invalid scores rejected."""
        for value in [True, 8, 8.0, None, "NaN", "Infinity", "-1", "11", "1e1", "01", "1.0000001"]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                calculate_score(RUBRIC, {"content": value, "structure": "6"})
        for scores in [{"content": "8"}, {**SCORES, "invented": "1"}, ["8", "6"]]:
            with self.subTest(scores=scores), self.assertRaises(ValidationError):
                calculate_score(RUBRIC, scores)

    def test_exact_half_cent_after_recurring_division(self):
        # Independent review regression: exact 50.005 must be rounded once to 50.01.
        """REQ-FUNC-004 / REQ-INV-005: exact half cent after recurring division."""
        rubric = {"id": "tie", "version": "1", "criteria": [
            {"id": str(i), "description": "x", "max_score": maximum, "weight": weight}
            for i, (weight, maximum) in enumerate(zip(["0.4", "0.1", "0.1", "0.4"], ["6", "6", "6", "1"]))]}
        self.assertEqual(calculate_score(rubric, {"0": "5", "1": "5", "2": "5", "3": "0.000125"}), "50.01")

    def test_invalid_rubric_rejected(self):
        """REQ-FUNC-001: invalid rubric rejected."""
        for field, value in [("weight", "0"), ("weight", "-1"), ("weight", "0.5"),
                             ("max_score", "0"), ("max_score", "NaN"), ("description", "")]:
            rubric = copy.deepcopy(RUBRIC)
            rubric["criteria"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                validate_rubric(rubric)
        rubric = copy.deepcopy(RUBRIC)
        rubric["criteria"][1]["id"] = "content"
        with self.assertRaises(ValidationError):
            validate_rubric(rubric)
        for rubric in [{**RUBRIC, "bonus": 1}, {**RUBRIC, "criteria": []}]:
            with self.assertRaises(ValidationError):
                validate_rubric(rubric)

    def test_json_duplicates_and_nonfinite_rejected(self):
        """REQ-FUNC-001 / REQ-SEC-007: json duplicates and nonfinite rejected."""
        for text in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{bad}', '[' * 2000]:
            with self.subTest(text=text[:30]), self.assertRaises(ValidationError):
                parse_json(text)

    def test_file_bounds_encoding_and_essay(self):
        """REQ-COST-005 / REQ-FUNC-001 / REQ-SEC-007: file bounds encoding and essay."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "text"
            path.write_bytes(b"12345")
            with self.assertRaises(ValidationError):
                read_text(path, 4)
            path.write_bytes(b"\xff")
            with self.assertRaises(ValidationError):
                read_text(path)
        for value in ["", "   ", "\ud800", None]:
            with self.assertRaises(ValidationError):
                validate_essay(value)


if __name__ == "__main__":
    unittest.main()
