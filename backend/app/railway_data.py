from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field, HttpUrl

class RailwayTrainingRecord(BaseModel):
    criticality: int = Field(ge=1, le=5)
    safety_risk: int = Field(ge=1, le=5)
    defect_severity: int = Field(ge=1, le=5)
    crew_size: int = Field(ge=1, le=100)
    machine: bool = False
    power_isolation: bool = False
    signal_disconnection: bool = False
    duration_minutes: float = Field(gt=0)
    failure_label: int = Field(ge=0, le=1)

class RailwayDataImport(BaseModel):
    source_name: str = Field(min_length=2, max_length=160)
    source_url: HttpUrl
    authority: str = Field(min_length=2, max_length=160)
    synthetic: bool = False
    records: list[RailwayTrainingRecord] = Field(min_length=10, max_length=100000)

IMPORTED_RECORDS: list[dict[str, Any]] = []
SOURCE_METADATA: dict[str, Any] = {'mode': 'SYNTHETIC_DEMO', 'source_name': 'SIH DEMO', 'records': 0}


def import_records(payload: RailwayDataImport) -> dict:
    global IMPORTED_RECORDS, SOURCE_METADATA
    IMPORTED_RECORDS = [record.model_dump() for record in payload.records]
    SOURCE_METADATA = {'mode': 'SYNTHETIC' if payload.synthetic else 'IMPORTED_REAL_DATA', 'source_name': payload.source_name, 'source_url': str(payload.source_url), 'authority': payload.authority, 'records': len(IMPORTED_RECORDS), 'imported_at': datetime.now(timezone.utc).isoformat()}
    return SOURCE_METADATA


def status() -> dict:
    return {**SOURCE_METADATA, 'model_training_source': 'imported records' if IMPORTED_RECORDS else 'synthetic maintenance history'}


def statistics() -> dict:
    if not IMPORTED_RECORDS:
        return {'source': status(), 'records': 0, 'message': 'Import authorized Indian Railway records to calculate operational statistics.'}
    durations = [record['duration_minutes'] for record in IMPORTED_RECORDS]
    failures = sum(record['failure_label'] for record in IMPORTED_RECORDS)
    return {'source': status(), 'records': len(IMPORTED_RECORDS), 'average_duration_minutes': round(sum(durations) / len(durations), 2), 'failure_rate': round(failures / len(IMPORTED_RECORDS), 4), 'critical_records': sum(record['criticality'] >= 4 for record in IMPORTED_RECORDS)}
