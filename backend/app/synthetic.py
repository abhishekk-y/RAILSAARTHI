from random import Random
from datetime import date
from .models import Station, Asset, Train, Task, Block, Scenario

STATIONS = [('SMP', 'Sampur Jn', 0), ('KAL', 'Kalyanpur', 18), ('NDP', 'Nandipur', 36), ('VKN', 'Vikas Nagar', 55), ('SHV', 'Shivapur Jn', 74)]
DEPTS = ['Engineering', 'S&T', 'TRD']


def priority_score(task: Task, traffic_density: int = 3) -> float:
    safety = 28 if task.safety_risk >= 4 else task.safety_risk * 4
    risk = task.defect_severity * 7
    overdue = max(0, task.deadline - 1440) / 1440 * 16
    impact = task.criticality * 5 + traffic_density * 2
    return round(min(100, safety + risk + overdue + impact), 1)


def generate_scenario(seed: int = 42, name: str = 'SIH DEMO') -> Scenario:
    rng = Random(seed)
    stations = [Station(id=i, name=n, km=k) for i, n, k in STATIONS]
    sections = [f'{STATIONS[i][0]}-{STATIONS[i+1][0]}' for i in range(4)]
    assets = []
    for index, section in enumerate(sections):
        assets.extend([
            Asset(id=f'TRK-{index+1:02}', name=f'{section} Up Main', asset_type='Track', section=section, criticality=4, health='ORANGE' if index % 2 else 'YELLOW'),
            Asset(id=f'SIG-{index+1:02}', name=f'{section} Home Signal', asset_type='Signal', section=section, criticality=5, health='RED' if index == 1 else 'YELLOW'),
            Asset(id=f'OHE-{index+1:02}', name=f'{section} OHE Section', asset_type='OHE', section=section, criticality=4, health='ORANGE'),
        ])
    trains = []
    for index, start in enumerate(range(20, 1440, 90)):
        section = sections[index % len(sections)]
        trains.append(Train(id=f'P-{index+1:03}', name=f'Intercity {index+1}', kind='PASSENGER', start=start, end=start+18, section=section))
    for index, start in enumerate([125, 330, 575, 810, 1030, 1280]):
        trains.append(Train(id=f'F-{index+1:03}', name=f'Freight {index+1}', kind='FREIGHT', start=start, end=start+24, section=sections[(index+1) % len(sections)]))
    tasks = []
    descriptions = {
        'Engineering': ['Rail weld inspection', 'Ballast tamping', 'Track geometry correction'],
        'S&T': ['Signal relay inspection', 'Axle counter calibration', 'Point machine test'],
        'TRD': ['OHE isolator inspection', 'Contact wire measurement', 'Section insulator replacement'],
    }
    for index in range(18):
        dept = DEPTS[index % 3]
        section = sections[index % 4]
        asset = next(a for a in assets if a.section == section and ((dept == 'Engineering' and a.asset_type == 'Track') or (dept == 'S&T' and a.asset_type == 'Signal') or (dept == 'TRD' and a.asset_type == 'OHE')))
        task = Task(id=f'{dept[:3].upper()}-{index+101}', department=dept, asset_id=asset.id, asset_type=asset.asset_type, section=section, description=descriptions[dept][index % 3], criticality=5 if index in [1, 7, 13] else rng.randint(3, 5), safety_risk=5 if index in [1, 7] else rng.randint(2, 4), defect_severity=rng.randint(2, 5), priority='P1' if index in [1, 7] else 'P2', deadline=360 + (index % 6) * 180, duration=35 + (index % 4) * 10, crew=f'{dept}-Crew-{index % 2 + 1}', crew_size=3 + index % 3, machine='Tamping Machine' if dept == 'Engineering' else None, power_isolation=dept == 'TRD', signal_disconnection=dept == 'S&T', preferred_start=90 + index * 15)
        task.priority_score = priority_score(task, 4 if section in sections[:2] else 2)
        tasks.append(task)
    fixed_blocks = [Block(id='FIX-01', section='SMP-KAL', start=420, end=450, task_ids=[], departments=['Engineering'], kind='Approved')]
    return Scenario(name=name, seed=seed, stations=stations, assets=assets, trains=trains, tasks=tasks, fixed_blocks=fixed_blocks)
