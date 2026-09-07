from typing import Literal
from pydantic import BaseModel, Field

Department = Literal['Engineering', 'S&T', 'TRD']

class Station(BaseModel):
    id: str
    name: str
    km: float

class Asset(BaseModel):
    id: str
    name: str
    asset_type: str
    section: str
    criticality: int
    health: Literal['GREEN', 'YELLOW', 'ORANGE', 'RED']

class Train(BaseModel):
    id: str
    name: str
    kind: Literal['PASSENGER', 'FREIGHT']
    start: int
    end: int
    section: str

class Task(BaseModel):
    id: str
    department: Department
    asset_id: str
    asset_type: str
    section: str
    description: str
    criticality: int = Field(ge=1, le=5)
    safety_risk: int = Field(ge=1, le=5)
    defect_severity: int = Field(ge=1, le=5)
    priority: str
    deadline: int
    duration: int
    crew: str
    crew_size: int
    machine: str | None = None
    power_isolation: bool = False
    signal_disconnection: bool = False
    preferred_start: int | None = None
    status: str = 'Pending'
    priority_score: float = 0

class Block(BaseModel):
    id: str
    section: str
    start: int
    end: int
    task_ids: list[str]
    departments: list[str]
    kind: str = 'Maintenance'

class Schedule(BaseModel):
    algorithm: str
    status: str
    blocks: list[Block]
    scheduled_task_ids: list[str]
    deferred_task_ids: list[str]
    objective: float
    runtime_ms: float
    constraint_count: int
    explanation: dict

class Scenario(BaseModel):
    name: str
    seed: int
    synthetic: bool = True
    generator_version: str = '1.0.0'
    stations: list[Station]
    assets: list[Asset]
    trains: list[Train]
    tasks: list[Task]
    fixed_blocks: list[Block]
