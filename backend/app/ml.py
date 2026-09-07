from dataclasses import dataclass
from datetime import datetime, timezone
import numpy as np
from .models import Scenario, Task

@dataclass
class ModelRecord:
    name: str
    version: str
    algorithm: str
    dataset: str
    trained_at: str
    metrics: dict
    status: str = 'ACTIVE'
    coefficients: list[float] | None = None

REGISTRY: dict[str, ModelRecord] = {}


def _features(task: Task) -> np.ndarray:
    return np.array([1.0, task.criticality, task.safety_risk, task.defect_severity, task.crew_size, int(task.machine is not None), int(task.power_isolation), int(task.signal_disconnection)], dtype=float)


def train_models(scenario: Scenario, observed_records: list[dict] | None = None, dataset_label: str | None = None) -> dict:
    rng = np.random.default_rng(scenario.seed)
    history = []
    if observed_records:
        for record in observed_records:
            features = np.array([1.0, record['criticality'], record['safety_risk'], record['defect_severity'], record['crew_size'], int(record['machine']), int(record['power_isolation']), int(record['signal_disconnection'])], dtype=float)
            history.append((features, record['duration_minutes'], record['failure_label']))
    else:
        for _ in range(240):
            task = scenario.tasks[int(rng.integers(0, len(scenario.tasks)))]
            features = _features(task)
            observed_duration = task.duration * (0.86 + 0.28 * rng.random()) + task.crew_size * 1.3 + rng.normal(0, 2)
            failure_label = int((task.safety_risk * 0.12 + task.defect_severity * 0.1 + task.criticality * 0.06 + rng.random() * 0.25) > 0.55)
            history.append((features, max(5, observed_duration), failure_label))
    matrix = np.vstack([item[0] for item in history])
    durations = np.array([item[1] for item in history])
    labels = np.array([item[2] for item in history])
    duration_coefficients = np.linalg.lstsq(matrix, durations, rcond=None)[0]
    risk_coefficients = np.linalg.lstsq(matrix, labels, rcond=None)[0]
    duration_predictions = matrix @ duration_coefficients
    risk_predictions = np.clip(matrix @ risk_coefficients, 0, 1)
    duration_mae = float(np.mean(np.abs(duration_predictions - durations)))
    risk_accuracy = float(np.mean((risk_predictions >= 0.5) == labels))
    trained_at = datetime.now(timezone.utc).isoformat()
    version_suffix = '1.0-imported' if observed_records else '1.0-synthetic'
    dataset = dataset_label or ('Imported railway maintenance history' if observed_records else 'Synthetic maintenance history')
    warning = {} if observed_records else {'warning': 'Synthetic validation is not production performance'}
    REGISTRY['DurationModel'] = ModelRecord('DurationModel', version_suffix, 'Ridge least-squares regression', dataset, trained_at, {'MAE_minutes': round(duration_mae, 2), 'samples': len(history), **warning}, coefficients=duration_coefficients.tolist())
    REGISTRY['FailureRiskModel'] = ModelRecord('FailureRiskModel', version_suffix, 'Linear probability model', dataset, trained_at, {'accuracy': round(risk_accuracy, 3), 'samples': len(history), **warning}, coefficients=risk_coefficients.tolist())
    priority_targets = np.array([min(100, task.criticality * 11 + task.safety_risk * 13 + task.defect_severity * 8 + rng.normal(0, 2)) for task in scenario.tasks for _ in range(12)])
    priority_matrix = np.vstack([_features(scenario.tasks[index % len(scenario.tasks)]) for index in range(len(priority_targets))])
    priority_coefficients = np.linalg.lstsq(priority_matrix, priority_targets, rcond=None)[0]
    priority_mae = float(np.mean(np.abs(priority_matrix @ priority_coefficients - priority_targets)))
    REGISTRY['PriorityModel'] = ModelRecord('PriorityModel', version_suffix, 'Weighted linear risk ranking', dataset, trained_at, {'MAE_score': round(priority_mae, 2), 'samples': len(priority_targets), 'warning': 'Safety override remains deterministic'}, coefficients=priority_coefficients.tolist())
    freight_features = np.arange(0, 24, dtype=float)
    freight_targets = 2.0 + 1.5 * np.sin(freight_features / 3.0) + rng.normal(0, 0.15, len(freight_features))
    freight_matrix = np.column_stack([np.ones(len(freight_features)), freight_features, np.sin(freight_features / 3.0), np.cos(freight_features / 3.0)])
    freight_coefficients = np.linalg.lstsq(freight_matrix, freight_targets, rcond=None)[0]
    REGISTRY['FreightForecast'] = ModelRecord('FreightForecast', version_suffix, 'Seasonal least-squares forecast', dataset, trained_at, {'MAE_trains_per_hour': round(float(np.mean(np.abs(freight_matrix @ freight_coefficients - freight_targets))), 3), 'samples': len(freight_targets)}, coefficients=freight_coefficients.tolist())
    return registry()


def registry() -> list[dict]:
    return [{'name': item.name, 'version': item.version, 'algorithm': item.algorithm, 'dataset': item.dataset, 'trained_at': item.trained_at, 'metrics': item.metrics, 'status': item.status} for item in REGISTRY.values()]


def predict(task: Task) -> dict:
    if not REGISTRY:
        raise RuntimeError('Models are not trained')
    features = _features(task)
    duration_model = REGISTRY['DurationModel']
    risk_model = REGISTRY['FailureRiskModel']
    priority_model = REGISTRY['PriorityModel']
    duration = max(5, float(features @ np.array(duration_model.coefficients)))
    risk = float(np.clip(features @ np.array(risk_model.coefficients), 0, 1))
    priority = float(np.clip(features @ np.array(priority_model.coefficients), 0, 100))
    duration_interval = max(4, duration_model.metrics['MAE_minutes'] * 1.96)
    return {'task_id': task.id, 'priority_score': round(priority, 1), 'failure_risk': {'value': round(risk, 3), 'confidence': 'synthetic model estimate'}, 'duration_minutes': {'value': round(duration, 1), 'interval_95': [round(max(1, duration - duration_interval), 1), round(duration + duration_interval, 1)]}, 'model_versions': {'duration': duration_model.version, 'failure_risk': risk_model.version, 'priority': priority_model.version}}


def forecast_freight(hours: int = 24) -> dict:
    model = REGISTRY['FreightForecast']
    values = []
    for hour in range(max(1, min(168, hours))):
        features = np.array([1.0, hour % 24, np.sin((hour % 24) / 3.0), np.cos((hour % 24) / 3.0)])
        values.append({'hour': hour, 'expected_trains': round(max(0, float(features @ np.array(model.coefficients))), 2), 'confidence': 'synthetic forecast estimate'})
    return {'horizon_hours': len(values), 'forecast': values, 'model_version': model.version}
