import re
from decimal import *
from datetime import datetime

import re
from decimal import Decimal


def numeric_conversion(value):

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    # Extract the first numeric value
    match = re.search(r"-?\d+(?:\.\d+)?", value)

    if not match:
        return None

    price = match.group()

    return Decimal(price).quantize(
        Decimal("0.001")
    )

from datetime import datetime, date


def date_conversion(arrival_date):
    """Convert supported source date formats to datetime.date.

    Supported formats:
    - YYYY-MM-DD
    - DD/MM/YYYY

    Return None for missing or invalid dates.
    """
    if arrival_date is None:
        return None

    if isinstance(arrival_date, datetime):
        return arrival_date.date()

    if isinstance(arrival_date, date):
        return arrival_date

    if not isinstance(arrival_date, str):
        return None

    value = arrival_date.strip()

    if not value:
        return None

    for date_format in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    return None
