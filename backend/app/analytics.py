from random import Random
from .models import Scenario, Schedule


def conflicts(scenario: Scenario, schedule: Schedule) -> list[dict]:
    task_map = {task.id: task for task in scenario.tasks}
    findings = []
    for block in schedule.blocks:
        task = task_map[block.task_ids[0]]
        for train in scenario.trains:
            if train.section == block.section and block.start < train.end + 8 and block.end > train.start - 8:
                findings.append({'type': 'TRAIN_CONFLICT', 'severity': 'HARD', 'block_id': block.id, 'train_id': train.id, 'message': f'{task.id} overlaps protected movement {train.id}'})
        for fixed in scenario.fixed_blocks:
            if fixed.section == block.section and block.start < fixed.end and block.end > fixed.start:
                findings.append({'type': 'APPROVED_BLOCK_CONFLICT', 'severity': 'HARD', 'block_id': block.id, 'fixed_block_id': fixed.id, 'message': f'{task.id} overlaps approved block {fixed.id}'})
    for index, left in enumerate(schedule.blocks):
        for right in schedule.blocks[index + 1:]:
            if left.section == right.section and left.start < right.end and left.end > right.start:
                findings.append({'type': 'SECTION_CONFLICT', 'severity': 'HARD', 'block_id': left.id, 'other_block_id': right.id, 'message': 'Two blocks occupy one section simultaneously'})
    return findings


def data_quality(scenario: Scenario) -> dict:
    checks = []
    task_ids = [task.id for task in scenario.tasks]
    checks.append({'rule': 'unique_task_ids', 'passed': len(task_ids) == len(set(task_ids)), 'count': len(task_ids)})
    checks.append({'rule': 'positive_durations', 'passed': all(task.duration > 0 for task in scenario.tasks), 'count': sum(task.duration <= 0 for task in scenario.tasks)})
    asset_ids = {asset.id for asset in scenario.assets}
    checks.append({'rule': 'asset_references', 'passed': all(task.asset_id in asset_ids for task in scenario.tasks), 'count': sum(task.asset_id not in asset_ids for task in scenario.tasks)})
    sections = {asset.section for asset in scenario.assets}
    checks.append({'rule': 'known_sections', 'passed': all(task.section in sections for task in scenario.tasks), 'count': sum(task.section not in sections for task in scenario.tasks)})
    score = round(sum(check['passed'] for check in checks) / len(checks) * 100, 1)
    return {'score': score, 'checks': checks, 'synthetic': scenario.synthetic}


def robustness(scenario: Scenario, schedule: Schedule, simulations: int = 100, seed: int = 42) -> dict:
    rng = Random(seed)
    task_map = {task.id: task for task in scenario.tasks}
    successful = 0
    passenger_delay = []
    for _ in range(simulations):
        valid = True
        delay_total = 0
        for block in schedule.blocks:
            task = task_map[block.task_ids[0]]
            duration = round(task.duration * (0.85 + rng.random() * 0.35))
            if block.end + max(0, duration - task.duration) > task.deadline:
                valid = False
            for train in scenario.trains:
                if train.section == block.section and block.start < train.end + 8 and block.start + duration > train.start - 8:
                    delay_total += max(0, block.start + duration - (train.start - 8))
        successful += int(valid and delay_total == 0)
        passenger_delay.append(delay_total)
    passenger_delay.sort()
    percentile_index = min(len(passenger_delay) - 1, round(len(passenger_delay) * 0.95))
    return {'simulations': simulations, 'seed': seed, 'robustness_score': round(successful / simulations * 100, 1), 'probability_all_tasks_complete': round(successful / simulations * 100, 1), 'expected_passenger_delay_min': round(sum(passenger_delay) / simulations, 1), 'p95_passenger_delay_min': passenger_delay[percentile_index]}
