"""
Database schema for the vessel schedule pipeline.

Works against SQLite (used for local dev / this demo) or Postgres in
production -- just point DATABASE_URL at either. Postgres is what we'd
recommend once more than one or two ports are live: better concurrent
write handling for scheduled jobs, native JSON columns, easier hosting
alongside a proper API.

Layer model:
  terminals        -- reference list of every source we scrape (config, not data)
  ingestion_runs    -- one row per scrape attempt, success or failure
  staging_raw       -- landing zone: near-verbatim rows as scraped, per run
  vessel_schedule   -- cleaned/normalised canonical table the frontend reads
  berthed_vessels   -- vessels currently alongside a berth, straight from each
                        terminal's own PDF -- deliberately separate from
                        vessel_schedule.status=='berthed' (which comes from the
                        JNPA master page instead; see the table's own docstring)
  alerts            -- anything an administrator should look at
"""
from datetime import datetime, timezone


def now_utc() -> datetime:
    """Naive UTC datetime (matches what SQLite/our scrapers already store)
    without the deprecation warning datetime.utcnow() now carries."""
    return datetime.now(timezone.utc).replace(tzinfo=None)



from sqlalchemy import (
    Boolean, Column, DateTime, Date, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Terminal(Base):
    """Config, not data: the list of sources the pipeline knows how to pull."""
    __tablename__ = "terminals"

    id = Column(Integer, primary_key=True)
    port_code = Column(String(16), nullable=False)          # 'JNPT'
    port_name = Column(String(128), nullable=False)         # 'Jawaharlal Nehru Port'
    terminal_code = Column(String(16), unique=True, nullable=False)  # 'NSICT'
    terminal_name = Column(String(128), nullable=False)
    operator = Column(String(128))                          # 'DP World'
    cargo_type = Column(String(32), nullable=False)         # container|liquid|dry_bulk|anchorage
    source_type = Column(String(16), nullable=False)        # 'html' | 'pdf'
    source_url = Column(String(512))
    is_container_terminal = Column(Boolean, default=False)
    active = Column(Boolean, default=True)


class IngestionRun(Base):
    """One row per attempt to pull one source. This is the audit trail the
    alerting logic and the frontend's status strip are both built on."""
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True)
    terminal_code = Column(String(16), nullable=False)
    scope = Column(String(16), nullable=False)               # 'master' | 'terminal'
    started_at = Column(DateTime, default=now_utc)
    finished_at = Column(DateTime)
    status = Column(String(16), nullable=False, default="running")  # running|success|partial|failed
    rows_found = Column(Integer, default=0)
    report_date = Column(Date)                                # date the SOURCE claims to be
    error_type = Column(String(32))                           # network|parse|schema_drift|empty
    error_message = Column(Text)

    staging_rows = relationship("StagingRaw", back_populates="run")
    alerts = relationship("Alert", back_populates="run")


class StagingRaw(Base):
    """Near-verbatim landing zone. We keep the original column labels from
    the source in raw_row_json so a format change is visible by diffing
    this table, even before normalisation logic is updated to match it."""
    __tablename__ = "staging_raw"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("ingestion_runs.id"), nullable=False)
    terminal_code = Column(String(16), nullable=False)
    section = Column(String(16), nullable=False)   # 'expected' | 'berthed' | 'sailed'
    raw_row_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now_utc)

    run = relationship("IngestionRun", back_populates="staging_rows")


class VesselSchedule(Base):
    """The clean databank the website reads from."""
    __tablename__ = "vessel_schedule"
    __table_args__ = (
        UniqueConstraint("terminal_code", "via_no", "status", "report_date",
                          name="uq_vessel_visit"),
    )

    id = Column(Integer, primary_key=True)
    port_code = Column(String(16), nullable=False)
    terminal_code = Column(String(16), nullable=False)
    berth_no = Column(String(32))
    status = Column(String(16), nullable=False)      # expected | berthed | sailed
    vessel_name = Column(String(128), nullable=False)
    via_no = Column(String(32))                       # voyage/call number, e.g. S1480
    service = Column(String(32))
    shipping_line = Column(String(64))
    agent = Column(String(128))                       # often unavailable at source; nullable
    loa_m = Column(Float)                              # length overall, metres
    cargo_commodity = Column(String(64))
    eta = Column(DateTime)
    gate_cutoff = Column(DateTime)  # gate closing deadline for an expected vessel's
                                     # cargo; only BMCT publishes this today (nullable
                                     # for every other terminal/status)
    berthed_on = Column(DateTime)
    expected_completion = Column(DateTime)
    sailed_on = Column(DateTime)
    report_date = Column(Date, nullable=False)
    source_run_id = Column(Integer, ForeignKey("ingestion_runs.id"))
    first_seen_at = Column(DateTime, default=now_utc)
    last_seen_at = Column(DateTime, default=now_utc)
    is_sample = Column(Boolean, default=False)  # True only for clearly-labelled demo rows


class BerthedVessel(Base):
    """Vessels currently alongside one of a terminal's own berths, scraped
    directly from that terminal's own PDF -- NOT the JNPA master page
    (which is where vessel_schedule.status=='berthed' rows come from).
    Kept as its own table rather than folded into vessel_schedule so the
    two sources -- one thin (master page: vessel/berth/via/times), one
    richer but terminal-specific (this table: berth side, alongside /
    ops-commenced / ops-completed timestamps, draft, moves) -- never
    collide or overwrite each other.

    Field coverage genuinely varies by terminal (see each scraper's
    docstring for exactly which columns it publishes); anything a given
    terminal doesn't print is left NULL rather than guessed.
    """
    __tablename__ = "berthed_vessels"
    __table_args__ = (
        UniqueConstraint("terminal_code", "via_no", "vessel_name", "report_date",
                          name="uq_berthed_vessel_visit"),
    )

    id = Column(Integer, primary_key=True)
    port_code = Column(String(16), nullable=False)
    terminal_code = Column(String(16), nullable=False)
    berth_no = Column(String(32))
    vessel_name = Column(String(128), nullable=False)
    via_no = Column(String(32))
    service = Column(String(32))
    shipping_line = Column(String(64))
    loa_m = Column(Float)
    draft_m = Column(Float)
    side = Column(String(16))              # PORT | STBD, where published
    alongside_at = Column(DateTime)         # when she came alongside the berth
    ops_commenced_at = Column(DateTime)
    ops_completed_at = Column(DateTime)     # NULL while operations are still ongoing
    next_event_at = Column(DateTime)        # ETD/ETC -- exact meaning varies by
                                             # terminal; see that scraper's docstring
    import_moves = Column(Integer)
    export_moves = Column(Integer)
    report_date = Column(Date, nullable=False)
    source_run_id = Column(Integer, ForeignKey("ingestion_runs.id"))
    first_seen_at = Column(DateTime, default=now_utc)
    last_seen_at = Column(DateTime, default=now_utc)


class Alert(Base):
    """Anything an administrator should look at. This is what a Slack/email
    notifier reads from -- it doesn't send anything itself."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("ingestion_runs.id"))
    terminal_code = Column(String(16), nullable=False)
    alert_type = Column(String(32), nullable=False)   # FETCH_FAILURE|PARSE_FAILURE|SCHEMA_DRIFT|STALE_DATA|ZERO_ROWS
    severity = Column(String(16), nullable=False)      # critical | warning
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now_utc)
    resolved = Column(Boolean, default=False)

    run = relationship("IngestionRun", back_populates="alerts")


def get_engine(database_url: str = "sqlite:///vessel_schedule.db"):
    return create_engine(database_url, future=True)


def get_session(engine):
    return sessionmaker(bind=engine, future=True)()


def init_db(engine):
    Base.metadata.create_all(engine)
