from datetime import date

from scripts.load_complaints import (
    blank_to_none,
    complaint_values,
    parse_date,
    yes_no_to_bool,
)


def test_blank_to_none():
    assert blank_to_none(" value ") == "value"
    assert blank_to_none("") is None
    assert blank_to_none("   ") is None


def test_yes_no_to_bool():
    assert yes_no_to_bool("Yes") is True
    assert yes_no_to_bool("No") is False
    assert yes_no_to_bool("") is None


def test_parse_date():
    assert parse_date("2026-07-13") == date(2026, 7, 13)
    assert parse_date("") is None


def test_complaint_values_maps_cfpb_columns():
    row = {
        "Complaint ID": "12345",
        "Date received": "2026-07-13",
        "Product": "Credit card",
        "Sub-product": "",
        "Issue": "Incorrect information",
        "Sub-issue": "",
        "Company": "Example Company",
        "State": "IL",
        "ZIP code": "60601",
        "Tags": "",
        "Submitted via": "Web",
        "Date sent to company": "2026-07-14",
        "Company response to consumer": "Closed with explanation",
        "Company public response": "",
        "Timely response?": "Yes",
        "Consumer complaint narrative": "Example complaint narrative.",
    }

    values = complaint_values(row, ingestion_run_id=7)

    assert values[0] == 12345
    assert values[1] == date(2026, 7, 13)
    assert values[2] == "Credit card"
    assert values[3] is None
    assert values[9] is None
    assert values[14] is True
    assert values[15] is None
    assert values[16] == "Example complaint narrative."
    assert values[17] == 7