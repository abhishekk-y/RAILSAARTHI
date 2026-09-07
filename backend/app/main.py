from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .synthetic import generate_scenario
from .optimizer import cp_sat, greedy, explain_task
from .kpi import calculate, compare
from .models import Train
from .joint_blocks import opportunities
from .realtime import hub
from .simulation import TwinState, event_stream, snapshot
from .replanning import replan_for_delay
from .analytics import conflicts, data_quality, robustness
from .integration import SyntheticAdapter
from .live_data import fetch_gtfs_realtime, fetch_osm_railway
from .ml import train_models, registry, predict, forecast_freight
from .railway_data import RailwayDataImport, import_records, status as data_source_status, statistics as data_statistics
from . import railway_data
from .workflow import seed_requests, list_requests, update_request, permissions
import csv
from io import StringIO

app = FastAPI(title='RailSaarthi API', version='0.1.0', description='Explainable railway maintenance block planning for synthetic demonstration data.')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
app.mount('/frontend', StaticFiles(directory=Path(__file__).resolve().parents[2] / 'frontend'), name='frontend')
SCENARIO = generate_scenario(); BASELINE = greedy(SCENARIO); OPTIMIZED = None
TWIN = TwinState(scenario_seed=SCENARIO.seed)
LIVE_DATA = {'map': None, 'trains': None, 'last_refresh': None}
MODEL_REGISTRY = train_models(SCENARIO)
seed_requests(SCENARIO)

@app.get('/api/health')
def health(): return {'api':'healthy','database':'demo-memory','optimizer':'ready','simulation':'available','synthetic':True}
@app.get('/api/scenario')
def scenario(): return SCENARIO.model_dump()
@app.post('/api/scenario/load')
def load(seed: int = 42):
    global SCENARIO, BASELINE, OPTIMIZED, TWIN, MODEL_REGISTRY; SCENARIO = generate_scenario(seed); BASELINE = greedy(SCENARIO); OPTIMIZED = None; TWIN = TwinState(scenario_seed=seed); MODEL_REGISTRY = train_models(SCENARIO, railway_data.IMPORTED_RECORDS or None, railway_data.SOURCE_METADATA.get('source_name')); seed_requests(SCENARIO); hub.publish({'type':'SCENARIO_LOADED','seed':seed}); return SCENARIO.model_dump()
@app.get('/api/tasks')
def tasks(): return [t.model_dump() for t in SCENARIO.tasks]
@app.get('/api/trains')
def trains(): return [t.model_dump() for t in SCENARIO.trains]

@app.get('/api/requests')
def maintenance_requests(department: str | None = None, status: str | None = None, priority: str | None = None): return {'count': len(list_requests(department, status, priority)), 'requests': list_requests(department, status, priority)}

@app.patch('/api/requests/{request_id}')
def change_request_status(request_id: str, status: str, actor_role: str = 'Control Office'):
    try:
        return update_request(request_id, status, actor_role)
    except PermissionError as error:
        raise HTTPException(403, str(error))
    except KeyError:
        raise HTTPException(404, 'Request not found')
    except ValueError as error:
        raise HTTPException(400, str(error))

@app.get('/api/roles/permissions')
def role_permissions(): return permissions()

@app.get('/api/search')
def search(query: str = '', kind: str = 'all', limit: int = 25):
    needle = query.strip().lower()
    cap = max(1, min(limit, 100))
    def matches(item: dict):
        return not needle or needle in ' '.join(str(value) for value in item.values()).lower()
    results = []
    if kind in {'all', 'trains'}:
        results.extend({'kind': 'train', 'id': train.id, 'label': train.name, 'detail': f'{train.kind} · {train.section} · {train.start:04d}-{train.end:04d}', 'record': train.model_dump()} for train in SCENARIO.trains if matches(train.model_dump()))
    if kind in {'all', 'tasks'}:
        results.extend({'kind': 'task', 'id': task.id, 'label': task.description, 'detail': f'{task.department} · {task.section} · {task.priority} · score {task.priority_score}', 'record': task.model_dump()} for task in SCENARIO.tasks if matches(task.model_dump()))
    if kind in {'all', 'assets'}:
        results.extend({'kind': 'asset', 'id': asset.id, 'label': asset.name, 'detail': f'{asset.asset_type} · {asset.section} · health {asset.health}', 'record': asset.model_dump()} for asset in SCENARIO.assets if matches(asset.model_dump()))
    return {'query': query, 'count': len(results[:cap]), 'results': results[:cap]}
@app.get('/api/blocks')
def blocks(algorithm: str = 'optimized'):
    schedule = OPTIMIZED or BASELINE if algorithm == 'optimized' else BASELINE
    return schedule.model_dump()
@app.post('/api/optimization/run')
def run_optimization(time_limit: float = 5.0):
    global OPTIMIZED; hub.publish({'type':'OPTIMIZATION_PROGRESS','status':'BUILDING_MODEL','progress':20}); OPTIMIZED = cp_sat(SCENARIO, time_limit); hub.publish({'type':'OPTIMIZATION_PROGRESS','status':'COMPLETE','progress':100,'solver_status':OPTIMIZED.status}); return {'run_id':'local-demo-run','schedule':OPTIMIZED.model_dump(),'comparison':compare(SCENARIO, BASELINE, OPTIMIZED),'joint_blocks': opportunities(SCENARIO, OPTIMIZED)}
@app.get('/api/metrics/availability')
def metrics(): return compare(SCENARIO, BASELINE, OPTIMIZED or BASELINE)
@app.get('/api/tasks/{task_id}/explanation')
def explanation(task_id: str):
    task = next((t for t in SCENARIO.tasks if t.id == task_id), None)
    if not task: raise HTTPException(404, 'Task not found')
    return explain_task(task, OPTIMIZED or BASELINE)

@app.get('/api/joint-blocks')
def joint_blocks(): return opportunities(SCENARIO, OPTIMIZED or BASELINE)

@app.post('/api/replan')
def replan(train_id: str, delay_minutes: int = 45):
    global SCENARIO, OPTIMIZED
    result = replan_for_delay(SCENARIO, OPTIMIZED or BASELINE, train_id, delay_minutes)
    SCENARIO = generate_scenario(result['scenario']['seed']); SCENARIO.trains = [Train(**item) for item in result['scenario']['trains']]
    OPTIMIZED = cp_sat(SCENARIO, 5.0); hub.publish({'type':'REPLAN_COMPLETE','train_id':train_id,'delay_minutes':delay_minutes,'status':OPTIMIZED.status}); return result

@app.get('/api/simulation/state')
def simulation_state(): return snapshot(SCENARIO, OPTIMIZED or BASELINE, TWIN.minute)

@app.post('/api/simulation/tick')
def simulation_tick(minutes: int = 5):
    TWIN.minute = min(1440, max(0, TWIN.minute + minutes)); state = snapshot(SCENARIO, OPTIMIZED or BASELINE, TWIN.minute); hub.publish({'type':'SIMULATION_TICK','minute':TWIN.minute,'clock':state['clock']}); return state

@app.get('/api/simulation/events')
def simulation_events(): return event_stream(SCENARIO, OPTIMIZED or BASELINE)

@app.get('/api/conflicts')
def conflict_report():
    findings = conflicts(SCENARIO, OPTIMIZED or BASELINE)
    return {'conflicts': findings, 'count': len(findings)}

@app.get('/api/data-quality')
def quality_report(): return data_quality(SCENARIO)

@app.get('/api/models')
def models(): return {'models': registry(), 'synthetic_training': True}

@app.post('/api/models/train')
def train_model_registry():
    global MODEL_REGISTRY
    MODEL_REGISTRY = train_models(SCENARIO, railway_data.IMPORTED_RECORDS or None, railway_data.SOURCE_METADATA.get('source_name'))
    hub.publish({'type': 'MODELS_TRAINED', 'models': len(MODEL_REGISTRY)})
    return {'models': MODEL_REGISTRY, 'synthetic_training': True}

@app.get('/api/models/predict/{task_id}')
def model_prediction(task_id: str):
    task = next((item for item in SCENARIO.tasks if item.id == task_id), None)
    if task is None: raise HTTPException(404, 'Task not found')
    return predict(task)

@app.get('/api/models/freight-forecast')
def freight_forecast(hours: int = 24): return forecast_freight(hours)

@app.post('/api/railway-data/import')
def import_railway_data(payload: RailwayDataImport):
    global MODEL_REGISTRY
    metadata = import_records(payload)
    MODEL_REGISTRY = train_models(SCENARIO, railway_data.IMPORTED_RECORDS, metadata['source_name'])
    hub.publish({'type': 'RAILWAY_DATA_IMPORTED', 'source': metadata['source_name'], 'records': metadata['records']})
    return {'source': metadata, 'statistics': data_statistics(), 'models': registry()}

@app.get('/api/railway-data/status')
def railway_data_status(): return data_source_status()

@app.get('/api/railway-data/statistics')
def railway_data_statistics(): return data_statistics()

@app.get('/api/robustness')
def robustness_report(simulations: int = 100): return robustness(SCENARIO, OPTIMIZED or BASELINE, max(10, min(1000, simulations)), SCENARIO.seed)

@app.get('/api/integration/status')
def integration_status(): return SyntheticAdapter().load(SCENARIO)

@app.get('/api/live/status')
def live_status():
    return {'mode': 'PUBLIC_WEB_DATA', 'map': {'available': LIVE_DATA['map'] is not None, 'source': 'OpenStreetMap Overpass API'}, 'trains': LIVE_DATA['trains'] or fetch_gtfs_realtime(), 'last_refresh': LIVE_DATA['last_refresh'], 'optimizer_input': 'Synthetic timetable unless a validated GTFS adapter is explicitly applied'}

@app.get('/api/live/map')
def live_map(lat: float = 28.6139, lon: float = 77.2090, radius: int = 12000):
    try:
        LIVE_DATA['map'] = fetch_osm_railway(lat, lon, max(1000, min(radius, 25000)))
        LIVE_DATA['last_refresh'] = LIVE_DATA['map']['fetched_at']
        return LIVE_DATA['map']
    except Exception as error:
        raise HTTPException(503, f'OpenStreetMap fetch failed: {error}')

@app.post('/api/live/refresh')
def refresh_live_data(lat: float = 28.6139, lon: float = 77.2090, radius: int = 12000, gtfs_url: str | None = None):
    map_data = fetch_osm_railway(lat, lon, max(1000, min(radius, 25000)))
    trains = fetch_gtfs_realtime(gtfs_url)
    LIVE_DATA['map'] = map_data
    LIVE_DATA['trains'] = trains
    LIVE_DATA['last_refresh'] = map_data['fetched_at']
    hub.publish({'type': 'LIVE_DATA_REFRESHED', 'map_features': len(map_data['features']), 'train_updates': len(trains.get('updates', []))})
    return {'map': map_data, 'trains': trains}

@app.get('/api/export/blocks.csv')
def export_blocks():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['block_id', 'section', 'start_minute', 'end_minute', 'task_ids', 'departments'])
    for block in (OPTIMIZED or BASELINE).blocks:
        writer.writerow([block.id, block.section, block.start, block.end, '|'.join(block.task_ids), '|'.join(block.departments)])
    return StreamingResponse(iter([output.getvalue()]), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename=railsaarthi-block-programme.csv'})

@app.websocket('/ws/events')
async def websocket_events(websocket: WebSocket): await hub.connect(websocket)

@app.get('/')
def index(): return FileResponse(Path(__file__).resolve().parents[2] / 'frontend' / 'index.html')
