import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

OSM_ENDPOINT = os.getenv('RAILSAARTHI_OVERPASS_URL', 'https://overpass-api.de/api/interpreter')
DEFAULT_LAT = float(os.getenv('RAILSAARTHI_MAP_LAT', '28.6139'))
DEFAULT_LON = float(os.getenv('RAILSAARTHI_MAP_LON', '77.2090'))
DEFAULT_RADIUS = int(os.getenv('RAILSAARTHI_MAP_RADIUS_M', '12000'))


def _get_json(url: str, params: dict | None = None) -> dict:
    if params:
        url = f'{url}?{urllib.parse.urlencode(params)}'
        request = urllib.request.Request(url, headers={'User-Agent': 'RailSaarthi/0.2 public-data-demo'})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode('utf-8'))


def _get_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={'User-Agent': 'RailSaarthi/0.2 public-data-demo'})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def fetch_osm_railway(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON, radius: int = DEFAULT_RADIUS) -> dict:
    query = f'''[out:json][timeout:18];(node(around:{radius},{lat},{lon})[railway~"station|halt|junction"];way(around:{radius},{lat},{lon})[railway~"rail|light_rail|subway"];);out geom;'''
    payload = _get_json(OSM_ENDPOINT, {'data': query})
    features = []
    for element in payload.get('elements', []):
        tags = element.get('tags', {})
        if element.get('type') == 'node':
            features.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [element['lon'], element['lat']]}, 'properties': {'id': element['id'], 'name': tags.get('name', 'Unnamed railway node'), 'railway': tags.get('railway', 'station')}})
        elif element.get('type') == 'way' and element.get('geometry'):
            features.append({'type': 'Feature', 'geometry': {'type': 'LineString', 'coordinates': [[point['lon'], point['lat']] for point in element['geometry']]}, 'properties': {'id': element['id'], 'name': tags.get('name', 'Railway track'), 'railway': tags.get('railway', 'rail')}})
    return {'type': 'FeatureCollection', 'features': features, 'source': 'OpenStreetMap Overpass API', 'attribution': '© OpenStreetMap contributors', 'center': {'lat': lat, 'lon': lon}, 'radius_m': radius, 'fetched_at': datetime.now(timezone.utc).isoformat()}


def fetch_gtfs_realtime(url: str | None = None) -> dict:
    feed_url = url or os.getenv('RAILSAARTHI_GTFS_RT_URL')
    if not feed_url:
        return {'enabled': False, 'source': 'GTFS-Realtime', 'message': 'Set RAILSAARTHI_GTFS_RT_URL to enable a public feed.'}
    try:
        from google.transit import gtfs_realtime_pb2
    except ImportError:
        return {'enabled': False, 'source': 'GTFS-Realtime', 'message': 'Install gtfs-realtime-bindings to decode the configured feed.'}
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(_get_bytes(feed_url))
    updates = []
    for entity in feed.entity:
        item = {'id': entity.id}
        if entity.HasField('trip_update'):
            item['trip_id'] = entity.trip_update.trip.trip_id
            item['route_id'] = entity.trip_update.trip.route_id
            item['delay_seconds'] = max((stop.arrival.delay for stop in entity.trip_update.stop_time_update if stop.HasField('arrival')), default=0)
            item['type'] = 'TRIP_UPDATE'
        if entity.HasField('vehicle'):
            item['vehicle_id'] = entity.vehicle.vehicle.id
            item['latitude'] = entity.vehicle.position.latitude
            item['longitude'] = entity.vehicle.position.longitude
            item['type'] = 'VEHICLE_POSITION'
        updates.append(item)
    return {'enabled': True, 'source': feed_url, 'fetched_at': datetime.now(timezone.utc).isoformat(), 'feed_timestamp': feed.header.timestamp, 'updates': updates}
