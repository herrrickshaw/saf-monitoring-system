from app.calculations.ghg import ghg_intensity, ghg_savings_pct, tco2e_saved


def test_ghg_intensity_sums_annex_v_terms():
    # e = eec + el + ep + etd + eu - esca - eccs - eccr - eee
    intensity = ghg_intensity(eec=1.0, el=0.0, ep=10.0, etd=2.0, eu=0.0, esca=1.0, eccs=0.0, eccr=0.0, eee=0.0)
    assert intensity == 1.0 + 10.0 + 2.0 - 1.0


def test_ghg_savings_pct_against_fossil_comparator():
    # Known worked example: intensity 13 gCO2eq/MJ vs 94 comparator -> ~86.2% savings
    savings = ghg_savings_pct(13.0, fossil_comparator=94.0)
    assert savings == round((1 - 13.0 / 94.0) * 100, 2)
    assert 85.0 < savings < 87.0


def test_tco2e_saved_scales_with_volume():
    small = tco2e_saved(1000, intensity=13.0, fossil_comparator=94.0)
    large = tco2e_saved(10000, intensity=13.0, fossil_comparator=94.0)
    assert large == round(small * 10, 3)
