import os
import sys
import types
import importlib.util
from importlib.machinery import SourceFileLoader

# --- Setup: ensure env vars so main.py doesn't raise on import ---
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "TEST_GOOGLE_KEY")
os.environ.setdefault("HF_TOKEN", "TEST_HF_TOKEN")

# --- Inject minimal fake 'smolagents' and 'gradio' to avoid side effects at import ---
class FakeCodeAgent:
    def __init__(self, *args, **kwargs):
        self.description = kwargs.get("description", "")
        self.tools = kwargs.get("tools", [])
        self.model = kwargs.get("model", None)
    def run(self, prompt):
        return "FAKE_AGENT_RESPONSE"

def fake_tool_decorator(fn):
    return fn

FakeSmol = types.SimpleNamespace(CodeAgent=FakeCodeAgent, tool=fake_tool_decorator, InferenceClientModel=lambda **k: None)
sys.modules.setdefault("smolagents", FakeSmol)

class FakeChatInterface:
    def __init__(self, fn=None, type=None, title=None):
        self.fn = fn
        self.type = type
        self.title = title
    def launch(self):
        return None

FakeGr = types.SimpleNamespace(ChatInterface=FakeChatInterface)
sys.modules.setdefault("gradio", FakeGr)

# --- Safely load the target module from the project file path ---
MAIN_PATH = os.path.join(os.path.dirname(__file__), "..", "main.py")
MAIN_PATH = os.path.normpath(MAIN_PATH)

loader = SourceFileLoader("calendar_main_for_tests", MAIN_PATH)
spec = importlib.util.spec_from_loader(loader.name, loader)
main = importlib.util.module_from_spec(spec)
loader.exec_module(main)

# --- Helper mock response class ---
class MockResponse:
    def __init__(self, status_code=200, json_data=None, text_data=""):
        self.status_code = status_code
        self._json = json_data
        self.text = text_data or ""
    def json(self):
        return self._json
    def raise_for_status(self):
        if self.status_code >= 400 and self.status_code != 409:
            raise Exception(f"HTTP {self.status_code}")

# --- Tests for calendar/location tools ---

def test_get_all_events_success(monkeypatch):
    sample = [{"id": "1", "title": "Meeting", "startDatetime": 1700000000, "endDatetime": 1700003600}]
    def fake_get(url, *args, **kwargs):
        return MockResponse(200, json_data=sample)
    monkeypatch.setattr("requests.get", fake_get)
    res = main.get_all_events()
    assert isinstance(res, list)
    assert res == sample

def test_get_event_by_id_success(monkeypatch):
    sample = {"id": "1", "title": "Event 1"}
    def fake_get(url, *args, **kwargs):
        assert url.endswith("/calendar/get/1")
        return MockResponse(200, json_data=sample)
    monkeypatch.setattr("requests.get", fake_get)
    res = main.get_event_by_id("1")
    assert isinstance(res, dict) and res["id"] == "1"

def test_get_all_locations_success(monkeypatch):
    sample = [{"name": "Office", "latitude": 1.1, "longitude": 2.2}]
    def fake_get(url, *a, **k):
        return MockResponse(200, json_data=sample)
    monkeypatch.setattr("requests.get", fake_get)
    res = main.get_all_locations()
    assert isinstance(res, list) and res == sample

def test_create_event_success_and_conflict(monkeypatch):
    payload_seen = {}
    def fake_post(url, json=None, *a, **k):
        payload_seen.update(json or {})
        return MockResponse(200, json_data={"id": "new_event", **(json or {})})
    monkeypatch.setattr("requests.post", fake_post)
    out = main.create_event("T", 1, 2, "Loc", 1.0, 2.0)
    assert isinstance(out, dict) and out.get("id") == "new_event"
    # conflict case
    def fake_post_conflict(url, json=None, *a, **k):
        return MockResponse(409, json_data={"error": "conflict"}, text_data="Conflict")
    monkeypatch.setattr("requests.post", fake_post_conflict)
    out2 = main.create_event("T", 1, 2, "Loc", 1.0, 2.0)
    assert isinstance(out2, str) and "already booked" in out2

def test_delete_event_success(monkeypatch):
    def fake_delete(url, *a, **k):
        return MockResponse(204, json_data=None, text_data="")
    monkeypatch.setattr("requests.delete", fake_delete)
    res = main.delete_event("123")
    assert "Successfully deleted" in res

def test_update_event_success_and_conflict(monkeypatch):
    def fake_post(url, json=None, *a, **k):
        return MockResponse(200, json_data={"id": "u1", **(json or {})})
    monkeypatch.setattr("requests.post", fake_post)
    out = main.update_event("u1", title="New")
    assert isinstance(out, dict) and out.get("id") == "u1"
    def fake_post_conflict(url, json=None, *a, **k):
        return MockResponse(409, json_data={"error": "conflict"})
    monkeypatch.setattr("requests.post", fake_post_conflict)
    out2 = main.update_event("u1", title="New")
    assert isinstance(out2, str) and "already booked" in out2

# --- Tests for geocoding and ETA tools ---

def test_get_lat_long_for_address_googlemaps_present(monkeypatch):
    # Inject fake googlemaps client into sys.modules for the function's import
    class FakeClient:
        def __init__(self, key=None):
            self.key = key
        def geocode(self, address):
            return [{"geometry": {"location": {"lat": 51.5, "lng": -0.1}}}]
    fake_gm = types.SimpleNamespace(Client=FakeClient, exceptions=types.SimpleNamespace(ApiError=Exception))
    monkeypatch.setitem(sys.modules, "googlemaps", fake_gm)
    res = main.get_lat_long_for_address("Dishoom shoreditch")
    assert isinstance(res, tuple) and len(res) == 2
    assert abs(res[0] - 51.5) < 1e-6

def test_get_lat_long_for_address_googlemaps_no_results(monkeypatch):
    class FakeClient:
        def __init__(self, key=None):
            pass
        def geocode(self, address):
            return []
    fake_gm = types.SimpleNamespace(Client=FakeClient, exceptions=types.SimpleNamespace(ApiError=Exception))
    monkeypatch.setitem(sys.modules, "googlemaps", fake_gm)
    res = main.get_lat_long_for_address("Unknown Place 12345")
    assert res is None

def test_get_eta_success(monkeypatch):
    # Mock the requests.post used by get_eta
    def fake_post(url, headers=None, json=None, *a, **k):
        data = {"routes": [{"duration": "15 mins", "distanceMeters": 12000}]}
        return MockResponse(200, json_data=data)
    monkeypatch.setattr("requests.post", fake_post)
    out = main.get_eta("Origin A", "Destination B")
    assert isinstance(out, str) and "ETA" in out or "current ETA" in out

# --- Tests for humanize_response formatting ---

def test_humanize_response_locations_and_events():
    locs = [{"name": "Office", "latitude": 1.0, "longitude": 2.0}]
    human_loc = main.humanize_response(locs, data_type="locations")
    assert "Office" in human_loc and "Lat" in human_loc

    events = [{"title": "Call", "startDatetime": 1700000000, "endDatetime": 1700003600, "location": {"name": "Office"}}]
    human_evt = main.humanize_response(events, data_type="events")
    assert "Call" in human_evt and "Office" in human_evt

# End of file
