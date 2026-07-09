"""Generates realistic sample data so every view/report in the app has something
to show: feedstock deliveries, production batches + certificates, airline
offtakes/deliveries, a carbon-credit ledger, and blending compliance records
(including one deliberately non-compliant airport to demonstrate the flag)."""

import random
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from ..calculations.astm_pathways import PATHWAYS, is_conformant
from ..calculations.corsia import credit_for_delivery, is_corsia_eligible
from ..calculations.ghg import FOSSIL_COMPARATOR_GCO2_PER_MJ, ghg_intensity, ghg_savings_pct
from ..models import (
    ASTMPathway,
    AirlineDelivery,
    AirlineOfftake,
    BlendingRecord,
    CarbonCreditLedger,
    Feedstock,
    FeedstockDelivery,
    ProductionBatch,
    SAFCertificate,
)

FEEDSTOCKS = [
    {
        "name": "Used Cooking Oil",
        "category": "IX-B",
        "supplier": "GreenCycle Oils BV",
        "default_eec": 1.0,
        "default_ep": 10.0,
        "default_etd": 2.0,
        "pathway_code": "HEFA-SPK",
    },
    {
        "name": "Animal Fat (Tallow)",
        "category": "IX-B",
        "supplier": "NordFett Rendering GmbH",
        "default_eec": 1.5,
        "default_ep": 12.0,
        "default_etd": 3.0,
        "pathway_code": "HEFA-SPK",
    },
    {
        "name": "Corn Stover Residue",
        "category": "IX-A",
        "supplier": "AgriResidue Co-op",
        "default_eec": 2.0,
        "default_ep": 15.0,
        "default_etd": 4.0,
        "pathway_code": "ATJ-SPK",
    },
]

AIRLINES = [
    {"airline_name": "Lufthansa Group", "delivery_airport": "EDDF", "contract_volume_liters": 5_000_000},
    {"airline_name": "British Airways", "delivery_airport": "EGLL", "contract_volume_liters": 4_000_000},
    {"airline_name": "Air France-KLM", "delivery_airport": "LFPG", "contract_volume_liters": 3_000_000},
]

RNG = random.Random(42)


def seed_if_empty(db: Session) -> None:
    if db.query(ASTMPathway).first():
        return  # already seeded

    pathways = {}
    for p in PATHWAYS:
        pathway = ASTMPathway(**p)
        db.add(pathway)
        db.flush()
        pathways[p["code"]] = pathway

    feedstocks = {}
    for f in FEEDSTOCKS:
        data = {k: v for k, v in f.items() if k != "pathway_code"}
        feedstock = Feedstock(**data)
        db.add(feedstock)
        db.flush()
        feedstocks[f["name"]] = feedstock

    today = date.today()
    batches = []
    for f in FEEDSTOCKS:
        feedstock = feedstocks[f["name"]]
        pathway = pathways[f["pathway_code"]]
        for months_ago in range(12, 0, -1):
            month_start = (today - relativedelta(months=months_ago)).replace(day=1)
            month_end = month_start + relativedelta(months=1) - timedelta(days=1)

            quantity_tonnes = round(RNG.uniform(500, 1500), 1)
            delivery = FeedstockDelivery(
                feedstock_id=feedstock.id,
                arrival_date=month_start + timedelta(days=RNG.randint(0, 5)),
                quantity_tonnes=quantity_tonnes,
                certificate_number=f"PoS-{feedstock.id}-{month_start:%Y%m}-{RNG.randint(1000, 9999)}",
                origin_country=RNG.choice(["Netherlands", "Germany", "France", "Spain", "Poland"]),
            )
            db.add(delivery)
            db.flush()

            saf_output_liters = round(quantity_tonnes * RNG.uniform(1100, 1300), 0)
            blend_ratio_pct = round(RNG.uniform(30.0, min(45.0, pathway.max_blend_pct)), 1)
            batch = ProductionBatch(
                batch_code=f"{pathway.code}-{feedstock.id}-{month_start:%Y%m}",
                start_date=month_start,
                end_date=month_end,
                astm_pathway_id=pathway.id,
                feedstock_delivery_id=delivery.id,
                feedstock_input_tonnes=quantity_tonnes,
                saf_output_liters=saf_output_liters,
                blend_ratio_pct=blend_ratio_pct,
                lab_certification_ref=f"LAB-CERT-{feedstock.id}-{month_start:%Y%m}",
                process_emissions_ep=feedstock.default_ep,
            )
            db.add(batch)
            db.flush()

            intensity = ghg_intensity(
                eec=feedstock.default_eec, el=0.0, ep=batch.process_emissions_ep, etd=feedstock.default_etd
            )
            savings_pct = ghg_savings_pct(intensity, FOSSIL_COMPARATOR_GCO2_PER_MJ)
            certificate = SAFCertificate(
                production_batch_id=batch.id,
                ghg_intensity=intensity,
                ghg_savings_pct=savings_pct,
                fossil_comparator=FOSSIL_COMPARATOR_GCO2_PER_MJ,
                eligible_feedstock=feedstock.category != "CROP",
                astm_conformant=is_conformant(pathway.max_blend_pct, blend_ratio_pct, batch.lab_certification_ref),
                corsia_eligible=is_corsia_eligible(savings_pct),
            )
            db.add(certificate)
            batches.append(batch)

    db.flush()

    offtakes = {}
    for a in AIRLINES:
        offtake = AirlineOfftake(
            airline_name=a["airline_name"],
            contract_volume_liters=a["contract_volume_liters"],
            delivery_airport=a["delivery_airport"],
            contract_start=today - relativedelta(years=1),
            contract_end=today + relativedelta(years=2),
        )
        db.add(offtake)
        db.flush()
        offtakes[a["airline_name"]] = offtake

    airline_cycle = list(offtakes.values())
    for i, batch in enumerate(batches):
        offtake = airline_cycle[i % len(airline_cycle)]
        volume = round(batch.saf_output_liters * RNG.uniform(0.5, 0.9), 0)
        delivery = AirlineDelivery(
            airline_offtake_id=offtake.id,
            production_batch_id=batch.id,
            volume_liters=volume,
            delivery_date=batch.end_date,
        )
        db.add(delivery)
        db.flush()

        certificate = batch.certificate
        tco2e = credit_for_delivery(volume, certificate.ghg_intensity, certificate.fossil_comparator)
        db.add(CarbonCreditLedger(airline_delivery_id=delivery.id, tco2e_saved=tco2e))

    # Blending compliance: EDDF compliant, EGLL deliberately short of mandate this year.
    current_year = today.year
    db.add(
        BlendingRecord(
            airport="EDDF",
            year=current_year,
            total_jet_fuel_liters=500_000_000,
            total_saf_liters=17_000_000,  # 3.4% actual vs ~2% mandate -> compliant
        )
    )
    db.add(
        BlendingRecord(
            airport="EGLL",
            year=current_year,
            total_jet_fuel_liters=420_000_000,
            total_saf_liters=4_000_000,  # ~0.95% actual vs ~2% mandate -> non-compliant
        )
    )
    db.add(
        BlendingRecord(
            airport="LFPG",
            year=current_year,
            total_jet_fuel_liters=380_000_000,
            total_saf_liters=9_500_000,  # ~2.5% actual -> compliant
        )
    )

    db.commit()
