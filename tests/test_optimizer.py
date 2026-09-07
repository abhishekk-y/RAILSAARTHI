from backend.app.synthetic import generate_scenario
from backend.app.optimizer import greedy
from fastapi.testclient import TestClient
from backend.app.main import app


def test_seed_is_reproducible():
    first = generate_scenario(42)
    second = generate_scenario(42)
    assert [task.model_dump() for task in first.tasks] == [task.model_dump() for task in second.tasks]


def test_greedy_respects_sections_and_deadlines():
    scenario = generate_scenario(42)
    schedule = greedy(scenario)
    for block in schedule.blocks:
        task = next(task for task in scenario.tasks if task.id in block.task_ids)
        assert block.end <= task.deadline
    for left in schedule.blocks:
        for right in schedule.blocks:
            if left.id != right.id and left.section == right.section:
                assert left.end <= right.start or right.end <= left.start


def test_realtime_workflow_routes():
    client = TestClient(app)
    client.post('/api/scenario/load?seed=42')
    optimized = client.post('/api/optimization/run').json()
    assert optimized['schedule']['status'] in {'OPTIMAL', 'FEASIBLE'}
    assert isinstance(optimized['joint_blocks'], list)
    assert client.post('/api/simulation/tick?minutes=15').json()['clock'] == '00:15'
    replanned = client.post('/api/replan?train_id=F-001&delay_minutes=45').json()
    assert replanned['new_plan']['status'] in {'OPTIMAL', 'FEASIBLE'}


def test_trained_model_workflow():
    client = TestClient(app)
    models = client.get('/api/models').json()['models']
    assert {model['name'] for model in models} == {'DurationModel', 'FailureRiskModel', 'PriorityModel', 'FreightForecast'}
    prediction = client.get('/api/models/predict/ENG-101').json()
    assert prediction['duration_minutes']['interval_95'][0] < prediction['duration_minutes']['value'] < prediction['duration_minutes']['interval_95'][1]
    assert 0 <= prediction['failure_risk']['value'] <= 1
    assert 'priority' in prediction['model_versions']
    assert len(client.get('/api/models/freight-forecast?hours=24').json()['forecast']) == 24
    assert client.post('/api/models/train').status_code == 200


def test_traffic_what_if_workflow():
    client = TestClient(app)
    result = client.post('/api/what-if/traffic?freight_multiplier=1.2&passenger_delay_minutes=0')
    assert result.status_code == 200
    payload = result.json()
    assert payload['assumptions']['freight_multiplier'] == 1.2
    assert 'comparison' in payload
    assert payload['new_plan']['status'] in {'OPTIMAL', 'FEASIBLE'}
