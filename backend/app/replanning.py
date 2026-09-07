from copy import deepcopy
from .models import Scenario, Schedule
from .optimizer import cp_sat
from .kpi import compare


def replan_for_delay(scenario: Scenario, baseline: Schedule, train_id: str, delay_minutes: int) -> dict:
    changed = deepcopy(scenario)
    train = next((item for item in changed.trains if item.id == train_id), None)
    if train is None:
        raise ValueError(f'Unknown train: {train_id}')
    train.start += delay_minutes
    train.end += delay_minutes
    revised = cp_sat(changed, 5.0)
    return {'trigger': {'type': 'TRAIN_DELAY', 'train_id': train_id, 'delay_minutes': delay_minutes}, 'old_plan': baseline.model_dump(), 'new_plan': revised.model_dump(), 'comparison': compare(changed, baseline, revised), 'changes': {'tasks_moved': sorted(set(baseline.scheduled_task_ids) ^ set(revised.scheduled_task_ids)), 'blocks_changed': abs(len(baseline.blocks) - len(revised.blocks))}, 'scenario': changed.model_dump()}
