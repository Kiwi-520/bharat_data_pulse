from datetime import date
from decimal import Decimal

import pytest

from ingestion.clean import numeric_conversion, date_conversion


class TestNumericConversion:
    """Tests for converting source prices into Decimal values with 3 places."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (1700, Decimal("1700.000")),
            (1700.5, Decimal("1700.500")),
            ("1700.50", Decimal("1700.500")),
            # Real edge case: source data contains integer strings without decimals.
            ("1600", Decimal("1600.000")),
            (" 1600 ", Decimal("1600.000")),
            ("1700.123456", Decimal("1700.123")),
        ],
    )
    def test_valid_numeric_values(self, value, expected):
        assert numeric_conversion(value) == expected

    @pytest.mark.parametrize(
        "value",
        [None, "", "   ", "N/A", "unknown"],
    )
    def test_missing_or_invalid_values(self, value):
        assert numeric_conversion(value) is None

    @pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", "inf", "-inf"])
    def test_non_finite_values(self, value):
        assert numeric_conversion(value) is None

    def test_large_numeric_string_does_not_return_infinity(self):
        result = numeric_conversion("1e309")
        assert result is None or result.is_finite()


class TestDateConversion:
    """Tests for parsing source dates using day-first date formats."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("01/01/2026", date(2026, 1, 1)),
            ("28/02/2026", date(2026, 2, 28)),
            ("02/01/2026", date(2026, 1, 2)),
        ],
    )
    def test_valid_day_first_dates(self, value, expected):
        assert date_conversion(value) == expected

    def test_day_and_month_are_not_confused(self):
        result = date_conversion("02/01/2026")

        assert result.day == 2
        assert result.month == 1
        assert result.year == 2026

    @pytest.mark.parametrize(
        "value",
        [None, "", "   ", "not-a-date", "32/01/2026", "29/02/2026"],
    )
    def test_missing_or_invalid_dates(self, value):
        assert date_conversion(value) is None
