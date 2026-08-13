from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))  # anthropic | openai | google | custom
    name: Mapped[str] = mapped_column(String(100))
    encrypted_key: Mapped[str] = mapped_column(Text)
    base_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # unverified | verified | invalid
    status: Mapped[str] = mapped_column(String(20), default="unverified")
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    scans: Mapped[list["Scan"]] = relationship(back_populates="provider")


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    git_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    scans: Mapped[list["Scan"]] = relationship(back_populates="target")


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("targets.id"))
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    model_id: Mapped[str] = mapped_column(String(100))
    application_id: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="queued")
    # queued | cloning | estimating | scanning | ingesting | succeeded | failed | canceled
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimate_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sarif_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    target: Mapped[Target] = relationship(back_populates="scans")
    provider: Mapped[Provider] = relationship(back_populates="scans")
    findings: Mapped[list["Finding"]] = relationship(back_populates="scan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"))
    rule_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # error | warning | note | none
    severity: Mapped[str] = mapped_column(String(20), default="warning")
    cwe: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file: Mapped[str | None] = mapped_column(String(500), nullable=True)
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[str] = mapped_column(String(30), default="open")
    # open | confirmed | false_positive | accepted_risk | fixed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    scan: Mapped[Scan] = relationship(back_populates="findings")
