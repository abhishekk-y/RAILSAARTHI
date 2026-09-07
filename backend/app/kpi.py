from .models import Scenario, Schedule

def calculate(scenario: Scenario, schedule: Schedule) -> dict:
    total = sum(t.duration for t in scenario.tasks); scheduled = sum(t.duration for t in scenario.tasks if t.id in schedule.scheduled_task_ids); trains = len(scenario.trains); delay = sum(max(0, b.end-b.start-20) for b in schedule.blocks for t in scenario.trains if t.section == b.section and b.start < t.end and b.end > t.start)
    joint = sum(1 for b in schedule.blocks if len(b.departments) > 1)
    return {'asset_availability': round(100 - scheduled / max(1, total) * 22, 2), 'infrastructure_downtime_min': scheduled, 'train_delay_min': delay, 'blocks_required': len(schedule.blocks), 'joint_blocks': joint, 'critical_tasks_completed': sum(1 for t in scenario.tasks if t.priority == 'P1' and t.id in schedule.scheduled_task_ids), 'overdue_maintenance': len(schedule.deferred_task_ids), 'maintenance_yield': round(len(schedule.scheduled_task_ids) / max(1, scheduled) * 100, 2), 'deadline_compliance': round(len(schedule.scheduled_task_ids) / max(1, len(scenario.tasks)) * 100, 2), 'robustness': round(max(0, 100 - len(schedule.deferred_task_ids) * 2 - delay * 0.2), 2), 'schedule_stability': 100.0}

def compare(scenario: Scenario, baseline: Schedule, optimized: Schedule) -> dict:
    before, after = calculate(scenario, baseline), calculate(scenario, optimized); return {'baseline': before, 'optimized': after, 'delta': {key: round(after[key] - before[key], 2) for key in before if isinstance(before[key], (int, float))}}
