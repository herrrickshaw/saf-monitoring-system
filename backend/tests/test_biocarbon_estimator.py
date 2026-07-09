from app.calculations import biocarbon_estimator


def test_estimate_credit_per_year_known_feedstock():
    # 200 TPD agri waste * 300 days * 0.35 tCO2e/tonne = 21,000
    credit = biocarbon_estimator.estimate_credit_per_year("agri_waste", 200)
    assert credit == 21000.0


def test_estimate_credit_per_year_unknown_feedstock_is_none():
    assert biocarbon_estimator.estimate_credit_per_year("unobtainium", 200) is None


def test_all_upneda_reference_feedstocks_present():
    expected = {
        "agri_waste", "animal_waste", "bagasse", "corn_cob", "msw",
        "napier_grass", "press_mud", "used_palm_cooking_oil", "waste_grains", "other",
    }
    assert set(biocarbon_estimator.FEEDSTOCK_TYPES.keys()) == expected


def test_higher_capacity_yields_more_credit():
    low = biocarbon_estimator.estimate_credit_per_year("bagasse", 100)
    high = biocarbon_estimator.estimate_credit_per_year("bagasse", 200)
    assert high == low * 2
