from .models import Scenario

class SyntheticAdapter:
    source_name = 'SYNTHETIC_DEMO'
    def load(self, scenario: Scenario) -> dict:
        return {'source': self.source_name, 'synthetic': scenario.synthetic, 'records': {'tasks': len(scenario.tasks), 'trains': len(scenario.trains), 'assets': len(scenario.assets)}}

class CSVAdapter:
    source_name = 'CSV'
    def load(self, path: str) -> dict:
        return {'source': self.source_name, 'path': path, 'status': 'CONTRACT_READY', 'message': 'Map CSV records into canonical models before scheduling.'}

class RESTAdapter:
    source_name = 'REST'
    def load(self, endpoint: str) -> dict:
        return {'source': self.source_name, 'endpoint': endpoint, 'status': 'CONTRACT_READY', 'message': 'Production authentication and schema mapping are required.'}
