from decimal import Decimal
from datetime import date
from ingestion.clean import numeric_conversion, date_conversion


class TestNumericConversion:

    def test_plain_integer(self):
        assert numeric_conversion(1700) == Decimal("1700.000")

    def test_plain_float(self):
        assert numeric_conversion(1700.5) == Decimal("1700.500")

    def test_string_with_decimal(self):
        assert numeric_conversion("1700.50") == Decimal("1700.500")

    def test_string_without_decimal(self):
        # real edge case found in 2009-era source data: "1600" with no decimal point
        assert numeric_conversion("1600") == Decimal("1600.000")

    def test_rounding_to_three_places(self):
        result = numeric_conversion(1700.123456)
        assert result == Decimal("1700.123")


class TestDateConversion:

    def test_standard_day_first_format(self):
        assert date_conversion("01/01/2026") == date(2026, 1, 1)

    def test_end_of_month(self):
        assert date_conversion("28/02/2026") == date(2026, 2, 28)

    def test_day_and_month_not_confused(self):
        # 02/01/2026 must parse as 2nd January, not 1st February
        result = date_conversion("02/01/2026")
        assert result.day == 2
        assert result.month == 1