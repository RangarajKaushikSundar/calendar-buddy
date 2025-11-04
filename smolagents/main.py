import json
import gradio as gr
import requests
import os
from datetime import datetime
from smolagents import CodeAgent, tool, InferenceClientModel

# --- Configuration ---
CALENDAR_API_BASE = "http://localhost:3000"
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
HF_API_TOKEN=os.getenv("HF_TOKEN")

if not GOOGLE_MAPS_API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set.")

# --- Tool Definitions ---

@tool
def get_all_events() -> list | str:
    """
    Gets all events from the calendar.
    Returns a list of event objects.
    """
    import datetime
    try:
        response = requests.get(f"{CALENDAR_API_BASE}/calendar/get")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"Error fetching events: {e}"

@tool
def get_event_by_id(event_id: str) -> dict | str:
    """
    Gets a specific event by its ID.

    Args:
        event_id: The ID of the event to retrieve.
    """
    try:
        response = requests.get(f"{CALENDAR_API_BASE}/calendar/get/{event_id}")
        response.raise_for_status()
        return  response.json()
    except requests.exceptions.RequestException as e:
        return f"Error fetching event {event_id}: {e}"

@tool
def get_eta(origin: str, destination: str) -> str:
    """
    Calculates real-time ETA between an origin and destination using the new Google Maps Routes API.
    
    Args:
        origin (str): The starting point — either an address (e.g. "1600 Amphitheatre Parkway, Mountain View, CA")
            or a "latitude,longitude" pair.
        destination (str): The destination — either an address or "latitude,longitude" pair.

    Returns:
        str: A human-readable description of the estimated travel time and distance.
    """
    import requests

    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.staticDuration"
    }

    def parse_location(loc):
        try:
            lat, lng = map(float, loc.split(","))
            return {"latLng": {"latitude": lat, "longitude": lng}}
        except ValueError:
            return {"address": loc}

    body = {
        "origin": parse_location(origin),
        "destination": parse_location(destination),
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
        "departureTime": "now",
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()

        if "routes" not in data or not data["routes"]:
            return f"Google Routes API Error: No routes found. {data}"

        route = data["routes"][0]
        duration = route.get("duration", "Unknown duration")
        distance = route.get("distanceMeters", 0)

        return f"The current ETA from {origin} to {destination} is {duration} ({distance/1000:.1f} km)."

    except requests.exceptions.RequestException as e:
        return f"Error calling Google Routes API: {e}"

@tool
def get_all_locations() -> list:
    """
    Gets all known locations from the calendar service.
    Always returns a list. On error returns an empty list.
    """
    try:
        response = requests.get(f"{CALENDAR_API_BASE}/location/get")
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        # if API returns a single object or unexpected type, try to normalize
        return list(data) if data else []
    except requests.exceptions.RequestException:
        return []

@tool
def get_lat_long_for_address(address: str) -> tuple | None:
    """
    Uses the Google Maps Geocoding API to get latitude and longitude for an address.

    Args:
        address (str): The address to geocode, e.g., "Dishoom shoreditch".

    Returns:
        tuple or None: A tuple (latitude, longitude) on success, or None on failure.
    """
    # Prefer using the googlemaps client if it's available, otherwise fall back to the HTTP Geocoding API.
    try:
        import googlemaps
        from googlemaps.exceptions import ApiError
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

        geocode_result = gmaps.geocode(address)
        print(f"Geocode result: {geocode_result}")
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            latitude = location['lat']
            longitude = location['lng']
            print(f"✅ Success: Address '{address}' -> Lat: {latitude}, Lng: {longitude}")
            return latitude, longitude
        
        else:
            print(f"⚠️ Warning: Could not find coordinates for address: '{address}'")
            return None

    # Catch all relevant API errors, including geocoding issues
    except ApiError as e:
        print(f"❌ API Error: Check your API key, billing, or if the Geocoding API is enabled. Details: {e}")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return None

@tool
def create_event(title: str, start_datetime: int, end_datetime: int, location_name: str, latitude: float, longitude: float) -> dict | str:
    """
    Creates a new event in the calendar.

    Args:
        title: The title of the event, includes purpose or attendees information.
        start_datetime: The start time of the event as a Unix epoch timestamp.
        end_datetime: The end time of the event as a Unix epoch timestamp.
        location_name: The name of the location (e.g., 'Office - Shoreditch').
        latitude: The latitude of the location.
        longitude: The longitude of the location.
    """
    payload = {
        "title": title,
        "startDatetime": start_datetime,
        "endDatetime": end_datetime,
        "location": {
            "name": location_name,
            "latitude": latitude,
            "longitude": longitude,
        },
    }
    try:
        response = requests.post(f"{CALENDAR_API_BASE}/calendar/create", json=payload)
        if response.status_code == 409:
            return "Error: This time slot is already booked. Please choose a different time."
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"Error creating event: {e}"

@tool
def delete_event(event_id: str) -> str:
    """
    Deletes an event from the calendar by its ID.

    Args:
        event_id: The ID of the event to delete.
    """
    try:
        response = requests.delete(f"{CALENDAR_API_BASE}/calendar/{event_id}")
        response.raise_for_status()
        if response.status_code == 204:
            return f"Successfully deleted event {event_id}."
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error deleting event {event_id}: {e}"

@tool
def update_event(event_id: str, title: str = None, start_datetime: int = None, end_datetime: int = None) -> dict | str:
    """
    Updates an existing event in the calendar. Only include the fields that need to be updated.

    Args:
        event_id: The ID of the event to update.
        title: The new title for the event.
        start_datetime: The new start time as a Unix epoch timestamp.
        end_datetime: The new end time as a Unix epoch timestamp.
    """
    payload = {}
    if title is not None:
        payload["title"] = title
    if start_datetime is not None:
        payload["startDatetime"] = start_datetime
    if end_datetime is not None:
        payload["endDatetime"] = end_datetime

    if not payload:
        return "Error: You must provide at least one field to update (title, start_datetime, or end_datetime)."

    try:
        response = requests.post(f"{CALENDAR_API_BASE}/calendar/update/{event_id}", json=payload)
        if response.status_code == 409:
            return "Error: This time slot is already booked. Please choose a different time."
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"Error updating event {event_id}: {e}"

@tool
def humanize_response(data: dict | list | str, data_type: str = "generic") -> str:
    """
    Converts structured calendar/location JSON or Python data into a human-readable message.
    Args:
        data: The response_body to humanize (list, dict, or JSON string).
        data_type: One of 'locations', 'events', or 'generic' — controls formatting style.
    Returns:
        A friendly, readable text summary.
    """
    import datetime
    import json
    # Parse JSON string if needed
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return str(data)

    if not data:
        return "No data found."

    if data_type == "locations":
        lines = [
            f"📍 {loc['name']} (Lat: {loc['latitude']}, Lon: {loc['longitude']})"
            for loc in data
        ]
        return f"You have {len(data)} saved locations:\n" + "\n".join(lines)

    elif data_type == "events":
        import datetime
        lines = []
        for e in data:
            title = e["title"]
            start = datetime.datetime.fromtimestamp(e["startDatetime"]).strftime("%Y-%m-%d %H:%M")
            end = datetime.datetime.fromtimestamp(e["endDatetime"]).strftime("%Y-%m-%d %H:%M")
            loc = e.get("location", {}).get("name", "Unknown Location")
            lines.append(f"{title} at {loc} from {start} to {end}")
        
        
        if not lines:
            return "No events found."
        return f"You have {len(data)} events:\n" + "\n".join(lines)

    else:
        return json.dumps(data, indent=2)

# --- Agent Initialization ---

system_prompt = f"""
You are a helpful Calendar and Navigation assistant.
Your goal is to help the user manage their calendar and get travel times for their events.
IMPORTANT: You **must always** include `import datetime` before using it.” Today's date is {datetime.now().strftime('%Y-%m-%d %H:%M')}. You must convert all user-provided times to epoch timestamps. 
IMPORTANT: You **must never** return raw JSON or dicts to the user. Instead, use ``humanize_response(response_body, data_type)`` to process the JSON before returning.

You have access to the following tools:
- A calendar API to get, create, update, and delete events.
- A Google Maps API to calculate real-time ETAs and find coordinates for addresses.

When user asks to list all events for the day, follow this workflow:
1. Use the `get_all_events` to get all the events in the user's calendar
2. Use the current date and time infromation in epoch format and find all the events that happen later in the day by comparing startTimestamp for each event.
3. IMPORTANT: You **must never** include the latitude, longitude data in the response. You **must always** use ``humanize_response(response_body, data_type)`` to process the JSON before returning. Do not write your own code.

When user asks to list all events, follow this workflow:
1. Use the `get_all_events` to get all the events in the user's calendar
2. IMPORTANT: You **must never** include the latitude, longitude data in the response. You **must always** use ``humanize_response(response_body, data_type)`` to process the JSON before returning. Do not write your own code.

When a user asks to create an event, you must follow this workflow:
1.  Extract the event details from the user's request (title, date, time, duration, location name).
2.  Use the `get_all_locations` tool to see if the location name is already known.
3.  If the location is known, use its latitude and longitude.
4.  If the location is NOT known, ask the user for the full address of the location.
5.  Once you have the address, use the `get_lat_long_for_address` tool to get its coordinates.
6.  Convert the start and end times to epoch timestamps.
7.  Call the `create_event` tool with all the required information: title, startDatetime, endDatetime, location_name, latitude, and longitude.
8.  Confirm to the user that the event has been created, or inform them of any conflicts.

When a user asks to update an event:
1.  First, find the event the user is referring to, likely by using `get_all_events` and searching by name.
2.  Once you have the event ID, call the `update_event` tool with the `event_id` and any new details the user provided (name, start_datetime, end_datetime).
3.  You must convert any new times to epoch timestamps before calling the tool.
4.  Confirm to the user that the event has been updated.

When a user asks for an ETA to an event:
1.  Use `get_all_events` to find the event.
2.  Identify the event's location (latitude and longitude).
3.  If the user hasn't provided a starting point, ask for their current location.
4.  Use the `get_eta` tool with the user's origin and the event's destination coordinates.
5.  Present the ETA clearly to the user.

"""

agent = CodeAgent(
    description=system_prompt,
    tools=[
        get_all_events,
        get_event_by_id,
        create_event,
        update_event,
        delete_event,
        get_eta,
        get_all_locations,
        get_lat_long_for_address,
        humanize_response,
    ],
    model=InferenceClientModel(model_id="meta-llama/Llama-3.1-8B-Instruct", token=HF_API_TOKEN)
)

conversation = [
    {"role": "system", "content": system_prompt}
]

def chat_fn(message, history):
    conversation.append({"role": "user", "content": message})
    prompt = "\n".join([
        f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation
    ])
    result = agent.run(prompt)
    conversation.append({"role": "assistant", "content": result})
    # Safely stringify any non-string result
    if not isinstance(result, str):
        result = json.dumps(result, indent=2)
    return result

gr.ChatInterface(
    fn=chat_fn,
    type="messages",
    title="Calendar Agent"
).launch()
