from dataclasses import dataclass
from .models import Scenario, Schedule

@dataclass
class TwinState:
    minute: int = 0
    running: bool = False
    scenario_seed: int = 42


def snapshot(scenario: Scenario, schedule: Schedule, minute: int) -> dict:
    trains = [{'id': train.id, 'section': train.section, 'state': 'IN_SECTION' if train.start <= minute <= train.end else ('COMPLETED' if minute > train.end else 'UPCOMING')} for train in scenario.trains]
    blocks = [{'id': block.id, 'section': block.section, 'state': 'ACTIVE' if block.start <= minute <= block.end else ('COMPLETED' if minute > block.end else 'UPCOMING'), 'task_ids': block.task_ids} for block in schedule.blocks]
    active = [item for item in blocks if item['state'] == 'ACTIVE']
    return {'minute': minute, 'clock': f'{minute // 60:02d}:{minute % 60:02d}', 'trains': trains, 'blocks': blocks, 'active_blocks': active, 'asset_availability': round(100 - len(active) * 1.5, 2)}


def event_stream(scenario: Scenario, schedule: Schedule) -> list[dict]:
    events = []
    for train in scenario.trains:
        events.extend([{'minute': train.start, 'type': 'TRAIN_ENTER', 'entity_id': train.id, 'section': train.section}, {'minute': train.end, 'type': 'TRAIN_LEAVE', 'entity_id': train.id, 'section': train.section}])
    for block in schedule.blocks:
        events.extend([{'minute': block.start, 'type': 'BLOCK_START', 'entity_id': block.id, 'section': block.section}, {'minute': block.end, 'type': 'BLOCK_CLEAR', 'entity_id': block.id, 'section': block.section}])
    return sorted(events, key=lambda event: (event['minute'], event['type']))
