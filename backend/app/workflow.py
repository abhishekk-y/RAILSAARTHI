from datetime import datetime, timezone
from uuid import uuid4
from .models import Scenario

ROLE_PERMISSIONS = {
    'Administrator': ['view_all', 'submit_request', 'approve_request', 'reject_request', 'run_optimizer', 'export_reports', 'manage_conflicts'],
    'Control Office': ['view_all', 'approve_request', 'reject_request', 'run_optimizer', 'freeze_schedule', 'export_reports'],
    'Planner': ['view_all', 'submit_request', 'run_optimizer', 'export_reports'],
    'Engineering': ['view_department', 'submit_request', 'comment'],
    'S&T': ['view_department', 'submit_request', 'comment'],
    'TRD': ['view_department', 'submit_request', 'comment'],
    'Viewer': ['view_all'],
}

REQUESTS: list[dict] = []


def seed_requests(scenario: Scenario):
    global REQUESTS
    if REQUESTS:
        return
    REQUESTS = [{'request_id': f'REQ-{index+1:04}', 'task_id': task.id, 'department': task.department, 'description': task.description, 'section': task.section, 'priority': task.priority, 'priority_score': task.priority_score, 'duration': task.duration, 'status': 'Submitted', 'submitted_at': datetime.now(timezone.utc).isoformat(), 'submitted_by': f'{task.department} Planning Cell'} for index, task in enumerate(scenario.tasks)]


def list_requests(department: str | None = None, status: str | None = None, priority: str | None = None):
    result = REQUESTS
    if department:
        result = [item for item in result if item['department'] == department]
    if status:
        result = [item for item in result if item['status'].lower() == status.lower()]
    if priority:
        result = [item for item in result if item['priority'].lower() == priority.lower()]
    return result


def update_request(request_id: str, status: str, actor_role: str):
    allowed = {'Approved', 'Rejected', 'Under Review', 'Submitted'}
    if status not in allowed:
        raise ValueError('Unsupported request status')
    if status in {'Approved', 'Rejected'} and 'approve_request' not in ROLE_PERMISSIONS.get(actor_role, []):
        raise PermissionError(f'{actor_role} cannot approve or reject requests')
    request = next((item for item in REQUESTS if item['request_id'] == request_id), None)
    if request is None:
        raise KeyError(request_id)
    request['status'] = status
    request['updated_at'] = datetime.now(timezone.utc).isoformat()
    request['updated_by'] = actor_role
    return request


def permissions():
    return ROLE_PERMISSIONS
