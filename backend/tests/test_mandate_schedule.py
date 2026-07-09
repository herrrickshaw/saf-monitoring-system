from app.calculations.mandate_schedule import mandate_pct_for_year


def test_mandate_pct_known_years():
    assert mandate_pct_for_year(2025) == 2.0
    assert mandate_pct_for_year(2030) == 6.0
    assert mandate_pct_for_year(2050) == 70.0


def test_mandate_pct_before_schedule_start_is_zero():
    assert mandate_pct_for_year(2024) == 0.0


def test_mandate_pct_after_schedule_end_holds_last_value():
    assert mandate_pct_for_year(2060) == 70.0
