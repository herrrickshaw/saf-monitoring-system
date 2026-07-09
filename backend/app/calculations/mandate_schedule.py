"""ReFuelEU Aviation minimum SAF blending share by year, per (EU) 2023/2405.

Editable defaults -- confirm against the current Regulation before compliance use;
percentages here are the headline minimum SAF share of aviation fuel uplifted at
Union airports (a separate synthetic-fuel sub-mandate also applies from 2030 and
is tracked separately, not enforced by this schedule).
"""

MANDATE_SCHEDULE_PCT = {
    2025: 2.0,
    2026: 2.0,
    2027: 2.0,
    2028: 2.0,
    2029: 2.0,
    2030: 6.0,
    2031: 6.0,
    2032: 6.0,
    2033: 6.0,
    2034: 6.0,
    2035: 20.0,
    2036: 20.0,
    2037: 20.0,
    2038: 20.0,
    2039: 20.0,
    2040: 34.0,
    2041: 34.0,
    2042: 34.0,
    2043: 34.0,
    2044: 34.0,
    2045: 42.0,
    2046: 42.0,
    2047: 42.0,
    2048: 42.0,
    2049: 42.0,
    2050: 70.0,
}


def mandate_pct_for_year(year: int) -> float:
    if year in MANDATE_SCHEDULE_PCT:
        return MANDATE_SCHEDULE_PCT[year]
    years = sorted(MANDATE_SCHEDULE_PCT)
    if year < years[0]:
        return 0.0
    return MANDATE_SCHEDULE_PCT[years[-1]]
