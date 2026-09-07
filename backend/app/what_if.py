from copy import deepcopy
from .models import Scenario, Schedule
from .optimizer import cp_sat
from .kpi import compare


def traffic_scenario(scenario: Scenario, baseline: Schedule, freight_multiplier: float = 1.2, passenger_delay_minutes: int = 0) -> dict:
    if freight_multiplier < 0.5 or freight_multiplier > 2.0:
        raise ValueError('freight_multiplier must be between 0.5 and 2.0')
    revised = deepcopy(scenario)
    for train in revised.trains:
        if train.kind == 'FREIGHT':
            train.start = int(train.start * freight_multiplier)
            train.end = int(train.end * freight_multiplier)
        elif passenger_delay_minutes:
            train.start += passenger_delay_minutes
            train.end += passenger_delay_minutes
    schedule = cp_sat(revised, 5.0)
    return {'assumptions': {'freight_multiplier': freight_multiplier, 'passenger_delay_minutes': passenger_delay_minutes}, 'old_plan': baseline.model_dump(), 'new_plan': schedule.model_dump(), 'comparison': compare(revised, baseline, schedule), 'changes': {'scheduled_tasks_moved': sorted(set(baseline.scheduled_task_ids) ^ set(schedule.scheduled_task_ids)), 'old_blocks': len(baseline.blocks), 'new_blocks': len(schedule.blocks)}, 'scenario': revised.model_dump()}
