from app.calculations import ccts_icm


def test_saf_not_yet_covered_under_ccts():
    # As of this writing, BEE has not notified SAF/aviation under CCTS.
    assert ccts_icm.is_saf_covered_under_ccts() is False


def test_compliance_mechanism_sectors_do_not_include_aviation():
    assert "Aviation" not in ccts_icm.COMPLIANCE_MECHANISM_SECTORS
    assert "SAF" not in ccts_icm.COMPLIANCE_MECHANISM_SECTORS
    assert len(ccts_icm.COMPLIANCE_MECHANISM_SECTORS) == 9


def test_ccc_surplus_when_actual_beats_target():
    # Entity emits less than its target -> earns surplus CCCs
    surplus = ccts_icm.ccc_surplus_deficit(
        actual_intensity_tco2e_per_unit=1.0, target_intensity_tco2e_per_unit=1.5, output_units=1000
    )
    assert surplus == 500.0


def test_ccc_deficit_when_actual_misses_target():
    # Entity emits more than its target -> owes CCCs
    deficit = ccts_icm.ccc_surplus_deficit(
        actual_intensity_tco2e_per_unit=2.0, target_intensity_tco2e_per_unit=1.5, output_units=1000
    )
    assert deficit == -500.0


def test_ccc_unit_is_one_tco2e():
    assert ccts_icm.CCC_UNIT_TCO2E == 1.0
