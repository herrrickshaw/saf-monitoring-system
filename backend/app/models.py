from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class ASTMPathway(Base):
    __tablename__ = "astm_pathways"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    annex: Mapped[str] = mapped_column(String)
    max_blend_pct: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String, default="")


class Feedstock(Base):
    __tablename__ = "feedstocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)  # IX-A | IX-B | CROP
    supplier: Mapped[str] = mapped_column(String)
    default_eec: Mapped[float] = mapped_column(Float, default=0.0)
    default_ep: Mapped[float] = mapped_column(Float, default=0.0)
    default_etd: Mapped[float] = mapped_column(Float, default=0.0)
    # CORSIA: key into calculations.corsia.DEFAULT_CORE_LCA_VALUES (with the
    # batch's ASTM pathway code); ILUC is 0 for waste/residue/by-product
    # feedstocks (ICAO default), non-zero only for main/primary products.
    corsia_feedstock_key: Mapped[str] = mapped_column(String, default="")
    corsia_iluc_value: Mapped[float] = mapped_column(Float, default=0.0)

    deliveries: Mapped[list["FeedstockDelivery"]] = relationship(back_populates="feedstock")


class FeedstockDelivery(Base):
    __tablename__ = "feedstock_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feedstock_id: Mapped[int] = mapped_column(ForeignKey("feedstocks.id"))
    arrival_date: Mapped[date] = mapped_column(Date)
    quantity_tonnes: Mapped[float] = mapped_column(Float)
    certificate_number: Mapped[str] = mapped_column(String)
    origin_country: Mapped[str] = mapped_column(String)

    feedstock: Mapped["Feedstock"] = relationship(back_populates="deliveries")


class ProductionBatch(Base):
    __tablename__ = "production_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_code: Mapped[str] = mapped_column(String, unique=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    astm_pathway_id: Mapped[int] = mapped_column(ForeignKey("astm_pathways.id"))
    feedstock_delivery_id: Mapped[int] = mapped_column(ForeignKey("feedstock_deliveries.id"))
    feedstock_input_tonnes: Mapped[float] = mapped_column(Float)
    saf_output_liters: Mapped[float] = mapped_column(Float)
    blend_ratio_pct: Mapped[float] = mapped_column(Float)
    lab_certification_ref: Mapped[str] = mapped_column(String, default="")
    process_emissions_ep: Mapped[float] = mapped_column(Float, default=0.0)

    astm_pathway: Mapped["ASTMPathway"] = relationship()
    feedstock_delivery: Mapped["FeedstockDelivery"] = relationship()
    certificate: Mapped["SAFCertificate"] = relationship(back_populates="batch", uselist=False)

    @property
    def yield_pct(self) -> float:
        if self.feedstock_input_tonnes <= 0:
            return 0.0
        # ~0.8 kg SAF per kg feedstock at density ~0.8 kg/L is a reasonable HEFA-class default
        output_tonnes = self.saf_output_liters * 0.0008
        return round((output_tonnes / self.feedstock_input_tonnes) * 100, 1)


class SAFCertificate(Base):
    __tablename__ = "saf_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    production_batch_id: Mapped[int] = mapped_column(ForeignKey("production_batches.id"), unique=True)
    # RED III / ReFuelEU (EU comparator, 94 gCO2eq/MJ)
    ghg_intensity: Mapped[float] = mapped_column(Float)
    ghg_savings_pct: Mapped[float] = mapped_column(Float)
    fossil_comparator: Mapped[float] = mapped_column(Float, default=94.0)
    eligible_feedstock: Mapped[bool] = mapped_column(Boolean)
    astm_conformant: Mapped[bool] = mapped_column(Boolean)
    # CORSIA (ICAO baseline, 89 gCO2e/MJ) -- see calculations/corsia.py
    corsia_core_lca_value: Mapped[float] = mapped_column(Float, default=0.0)
    corsia_lcef: Mapped[float] = mapped_column(Float, default=0.0)
    corsia_reduction_pct: Mapped[float] = mapped_column(Float, default=0.0)
    corsia_eligible: Mapped[bool] = mapped_column(Boolean)
    issued_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    batch: Mapped["ProductionBatch"] = relationship(back_populates="certificate")


class AirlineOfftake(Base):
    __tablename__ = "airline_offtakes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    airline_name: Mapped[str] = mapped_column(String)
    contract_volume_liters: Mapped[float] = mapped_column(Float)
    delivery_airport: Mapped[str] = mapped_column(String)
    contract_start: Mapped[date] = mapped_column(Date)
    contract_end: Mapped[date] = mapped_column(Date)

    deliveries: Mapped[list["AirlineDelivery"]] = relationship(back_populates="offtake")


class AirlineDelivery(Base):
    __tablename__ = "airline_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    airline_offtake_id: Mapped[int] = mapped_column(ForeignKey("airline_offtakes.id"))
    production_batch_id: Mapped[int] = mapped_column(ForeignKey("production_batches.id"))
    volume_liters: Mapped[float] = mapped_column(Float)
    delivery_date: Mapped[date] = mapped_column(Date)

    offtake: Mapped["AirlineOfftake"] = relationship(back_populates="deliveries")
    batch: Mapped["ProductionBatch"] = relationship()
    credit_ledger: Mapped["CarbonCreditLedger"] = relationship(back_populates="delivery", uselist=False)


class CarbonCreditLedger(Base):
    __tablename__ = "carbon_credit_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    airline_delivery_id: Mapped[int] = mapped_column(ForeignKey("airline_deliveries.id"), unique=True)
    tco2e_saved: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="calculated")  # calculated | reported
    calculated_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    delivery: Mapped["AirlineDelivery"] = relationship(back_populates="credit_ledger")


class BlendingRecord(Base):
    __tablename__ = "blending_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    airport: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)
    total_jet_fuel_liters: Mapped[float] = mapped_column(Float)
    total_saf_liters: Mapped[float] = mapped_column(Float)

    @property
    def actual_pct(self) -> float:
        if self.total_jet_fuel_liters <= 0:
            return 0.0
        return round((self.total_saf_liters / self.total_jet_fuel_liters) * 100, 3)
