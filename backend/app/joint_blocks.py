from collections import defaultdict
from .models import Scenario, Schedule

COMPATIBILITY = {
    frozenset({'Engineering', 'S&T'}): True,
    frozenset({'Engineering', 'TRD'}): True,
    frozenset({'S&T', 'TRD'}): False,
}


def opportunities(scenario: Scenario, schedule: Schedule) -> list[dict]:
    by_section = defaultdict(list)
    task_map = {task.id: task for task in scenario.tasks}
    for block in schedule.blocks:
        task = task_map[block.task_ids[0]]
        by_section[block.section].append((block, task))
    result = []
    for section, entries in by_section.items():
        entries.sort(key=lambda item: item[0].start)
        for index, (left_block, left_task) in enumerate(entries):
            for right_block, right_task in entries[index + 1:]:
                if right_block.start - left_block.end > 35:
                    break
                departments = frozenset({left_task.department, right_task.department})
                compatible = len(departments) == 1 or COMPATIBILITY.get(departments, False)
                if compatible and left_task.department != right_task.department:
                    independent = (left_block.end - left_block.start) + (right_block.end - right_block.start)
                    joint = max(left_block.end, right_block.end) - min(left_block.start, right_block.start)
                    result.append({'id': f'JNT-{len(result)+1:03}', 'section': section, 'task_ids': [left_task.id, right_task.id], 'departments': sorted(departments), 'independent_minutes': independent, 'joint_minutes': joint, 'minutes_saved': max(0, independent - joint), 'compatibility': 'EXPLICIT_RULE'})
    return result
