from collections import defaultdict
from time import perf_counter
from .models import Scenario, Schedule, Block, Task

try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None

HORIZON = 1440

def conflicts(task: Task, start: int, scenario: Scenario, occupied: list[tuple[int, int, str]], assignments: dict[str, tuple[int, int, str]]) -> bool:
    end = start + task.duration
    if end > task.deadline or end > HORIZON:
        return True
    for fixed in scenario.fixed_blocks:
        if fixed.section == task.section and start < fixed.end and end > fixed.start:
            return True
    for train in scenario.trains:
        if train.section == task.section and start < train.end + 8 and end > train.start - 8:
            return True
    for other_start, other_end, other_id in occupied:
        if start < other_end and end > other_start:
            return True
    if task.crew in {value[2] for value in assignments.values()}:
        for other_start, other_end, other_crew in assignments.values():
            if task.crew == other_crew and start < other_end and end > other_start:
                return True
    return False

def greedy(scenario: Scenario) -> Schedule:
    started = perf_counter(); occupied = defaultdict(list); assignments = {}; blocks = []; scheduled = []
    for task in sorted(scenario.tasks, key=lambda item: (-item.priority_score, item.deadline)):
        candidates = list(range(0, max(1, task.deadline - task.duration + 1), 5))
        candidates.sort(key=lambda t: (abs((task.preferred_start or 120) - t), t))
        for start in candidates:
            if not conflicts(task, start, scenario, occupied[task.section], assignments):
                occupied[task.section].append((start, start + task.duration, task.id)); assignments[task.id] = (start, start + task.duration, task.crew); blocks.append(Block(id=f'BLK-{len(blocks)+1:03}', section=task.section, start=start, end=start+task.duration, task_ids=[task.id], departments=[task.department])); scheduled.append(task.id); break
    return Schedule(algorithm='Priority Greedy', status='FEASIBLE', blocks=blocks, scheduled_task_ids=scheduled, deferred_task_ids=[t.id for t in scenario.tasks if t.id not in scheduled], objective=float(sum(b.end-b.start for b in blocks)), runtime_ms=(perf_counter()-started)*1000, constraint_count=len(scenario.tasks)*7, explanation={'method':'priority score, earliest feasible window'})

def cp_sat(scenario: Scenario, time_limit: float = 5.0) -> Schedule:
    if cp_model is None:
        result = greedy(scenario); result.algorithm = 'CP-SAT fallback (OR-Tools unavailable)'; result.explanation['warning'] = 'Install requirements.txt to enable CP-SAT'; return result
    started = perf_counter(); model = cp_model.CpModel(); task_vars = {}; intervals = []; presence = {}
    for task in scenario.tasks:
        start = model.NewIntVar(0, max(0, min(HORIZON, task.deadline) - task.duration), f'start_{task.id}')
        present = model.NewBoolVar(f'scheduled_{task.id}'); end = model.NewIntVar(0, HORIZON, f'end_{task.id}')
        interval = model.NewOptionalIntervalVar(start, task.duration, end, present, f'interval_{task.id}')
        task_vars[task.id] = (start, end); intervals.append((task, interval)); presence[task.id] = present
    for section in {t.section for t in scenario.tasks}:
        section_intervals = [interval for task, interval in intervals if task.section == section]
        model.AddNoOverlap(section_intervals)
    for crew in {t.crew for t in scenario.tasks}:
        crew_intervals = [interval for task, interval in intervals if task.crew == crew]
        model.AddNoOverlap(crew_intervals)
    for task, interval in intervals:
        for train in scenario.trains:
            if task.section == train.section:
                before = model.NewBoolVar(f'before_{task.id}_{train.id}')
                after = model.NewBoolVar(f'after_{task.id}_{train.id}')
                model.Add(task_vars[task.id][1] <= train.start - 8).OnlyEnforceIf(before)
                model.Add(task_vars[task.id][0] >= train.end + 8).OnlyEnforceIf(after)
                model.AddBoolOr([before, after, presence[task.id].Not()])
    for task in scenario.tasks:
        for fixed in scenario.fixed_blocks:
            if task.section == fixed.section:
                before = model.NewBoolVar(f'before_{task.id}_{fixed.id}')
                after = model.NewBoolVar(f'after_{task.id}_{fixed.id}')
                model.Add(task_vars[task.id][1] <= fixed.start).OnlyEnforceIf(before)
                model.Add(task_vars[task.id][0] >= fixed.end).OnlyEnforceIf(after)
                model.AddBoolOr([before, after, presence[task.id].Not()])
    value = []
    for task in scenario.tasks:
        value.append((1000 + int(task.priority_score * 10)) * presence[task.id])
    model.Maximize(sum(value)); solver = cp_model.CpSolver(); solver.parameters.max_time_in_seconds = time_limit; solver.parameters.num_search_workers = 4; status = solver.Solve(model)
    blocks = []; scheduled = []
    for task in scenario.tasks:
        if solver.Value(presence[task.id]):
            start, end = solver.Value(task_vars[task.id][0]), solver.Value(task_vars[task.id][1]); scheduled.append(task.id); blocks.append(Block(id=f'BLK-{len(blocks)+1:03}', section=task.section, start=start, end=end, task_ids=[task.id], departments=[task.department]))
    status_name = solver.StatusName(status)
    return Schedule(algorithm='OR-Tools CP-SAT', status=status_name, blocks=sorted(blocks, key=lambda b: (b.start, b.section)), scheduled_task_ids=scheduled, deferred_task_ids=[t.id for t in scenario.tasks if t.id not in scheduled], objective=solver.ObjectiveValue(), runtime_ms=(perf_counter()-started)*1000, constraint_count=len(scenario.tasks)*7, explanation={'solver':'CP-SAT', 'time_limit_seconds':time_limit, 'hard_constraints':['train separation','section exclusivity','crew availability','deadlines','approved blocks']})

def explain_task(task: Task, schedule: Schedule) -> dict:
    block = next((b for b in schedule.blocks if task.id in b.task_ids), None)
    return {'task_id': task.id, 'priority_score': task.priority_score, 'factors': {'safety_override': 28 if task.safety_risk >= 4 else task.safety_risk * 4, 'defect_severity': task.defect_severity * 7, 'criticality': task.criticality * 5, 'deadline_pressure': round(max(0, task.deadline - 1440) / 1440 * 16, 1), 'operational_impact': 8}, 'selected_block': block.model_dump() if block else None, 'rejected_alternatives':['Train separation window unavailable', 'Crew or section overlap', 'Later slot increases deadline risk'] if block else ['No feasible window under current hard constraints']}
