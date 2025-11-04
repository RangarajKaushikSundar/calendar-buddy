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
def get_eta(origin: str | dict, destination: str | dict) -> str:
    """
    Calculates real-time ETA between an origin and destination using the new Google Maps Routes API.
    
    Args:
        origin (str): The starting point — either an address (e.g. "1600 Amphitheatre Parkway, Mountain View, CA")
            or a "latitude,longitude" tuple string.
        destination (str): The destination — either an address or "latitude,longitude" tuple string.
        
    Returns:
        str: A human-readable description of the estimated travel time and distance.
    """
    import requests, datetime, json

    def format_location(loc):
        # If dict with lat/lng returned from get_lat_long_for_address
        if isinstance(loc, dict):
            if loc.get('error'):
                return {"error": loc['error']}
            return {"location": {"latLng": {"latitude": loc['lat'], "longitude": loc['lng']}}}
        # If string, treat as address
        elif isinstance(loc, str):
            return {"location": {"address": loc}}
        else:
            return {"error": "Invalid location format"}

    origin_loc = format_location(origin)
    destination_loc = format_location(destination)

    # Check for error before making API call
    if 'error' in origin_loc:
        return f"Error: {origin_loc['error']}"
    if 'error' in destination_loc:
        return f"Error: {destination_loc['error']}"

    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.staticDuration"
    }

    departure_time_iso = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    body = {
        "origin": origin_loc,
        "destination": destination_loc,
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
        "departureTime": departure_time_iso,
        "languageCode": "en-US",
        "units": "METRIC",
        "regionCode": "GB"
    }
    print(f"Requesting ETA with body: {json.dumps(body)}")
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()

        if "routes" not in data or not data["routes"]:
            return f"Google Routes API Error: No routes found. {data}"

        route = data["routes"][0]
        duration = route.get("duration", "Unknown duration")
        distance = route.get("distanceMeters", 0)
        return f"The current ETA is {duration} ({distance/1000:.1f} km)."

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
def get_lat_long_for_address(address: str) -> dict:
    """
    Uses the Google Maps Geocoding API to get latitude and longitude for an address.

    Args:
        address (str): The address to geocode, e.g., "Dishoom shoreditch".

    Returns:
        dict or None: A dictionary {'lat': latitude, 'lng': longitude} on success, or None on failure.
    """
    try:
        import googlemaps
        from googlemaps.exceptions import ApiError
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            latitude = location['lat']
            longitude = location['lng']
            formatted_address = geocode_result[0].get('formatted_address', address)
            print(f"Success: Address '{formatted_address}' -> Lat: {latitude}, Lng: {longitude}")
            return {'lat': latitude, 'lng': longitude, 'formatted_address': formatted_address}
        
        else:
            print(f"Warning: Could not find coordinates for address: '{address}'")
            return {'lat': None, 'lng': None, 'formatted_address': address, 'error': 'Address not found'}


    except ApiError as e:
        print(f"API Error: Check your API key, billing, or if the Geocoding API is enabled. Details: {e}")
        return {'lat': None, 'lng': None, 'formatted_address': address, 'error': str(e)}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {'lat': None, 'lng': None, 'formatted_address': address, 'error': str(e)}

@tool
def create_event(title: str, startDatetime: int, endDatetime: int, location_name: str, latitude: float, longitude: float) -> dict | str:
    """
    Creates a new event in the calendar.

    Args:
        title: The title of the event, includes purpose or attendees information.
        startDatetime: The start time of the event as a Unix epoch timestamp.
        endDatetime: The end time of the event as a Unix epoch timestamp.
        location_name: The name of the location (e.g., 'Office - Shoreditch').
        latitude: The latitude of the location.
        longitude: The longitude of the location.
    """
    payload = {
        "title": title,
        "startDatetime": startDatetime,
        "endDatetime": endDatetime,
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
def update_event(event_id: str, title: str = None, startDatetime: int = None, endDatetime: int = None) -> dict | str:
    """
    Updates an existing event in the calendar. Only include the fields that need to be updated.

    Args:
        event_id: The ID of the event to update.
        title: The new title for the event.
        startDatetime: The new start time as a Unix epoch timestamp.
        endDatetime: The new end time as a Unix epoch timestamp.
    """
    payload = {}
    if title is not None:
        payload["title"] = title
    if startDatetime is not None:
        payload["startDatetime"] = startDatetime
    if endDatetime is not None:
        payload["endDatetime"] = endDatetime

    if not payload:
        return "Error: You must provide at least one field to update (title, startDatetime, or endDatetime)."

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
        data_type: For locations use 'locations', for meetings, events and event use : 'events', or 'generic' — controls formatting style.
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

    if data_type.startswith("loc"):
        lines = [
            f"📍 {loc['name']} (Lat: {loc['latitude']}, Lon: {loc['longitude']})"
            for loc in data
        ]
        return f"You have {len(data)} saved locations:\n" + "\n".join(lines)

    elif data_type.startswith("event") or data_type.startswith("meet"):
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

# --- AGENT STUFF ---

system_prompt = f"""
You are a helpful Calendar and Navigation assistant.
Your goal is to help the user manage their calendar and get travel times for their events.
IMPORTANT: You **must always** include `import datetime` before using it.” Today's date is {datetime.now().strftime('%Y-%m-%d %H:%M')}. You must convert all user-provided times to epoch timestamps. 
EXTREMELY IMPORTANT: You **must never** return raw JSON or dicts to the user. You must use ``humanize_response(response_body, data_type)`` to process the JSON before returning.

You have access to the following tools:
- A calendar API to get, create, update, and delete events.
- A Google Maps API to calculate real-time ETAs and find coordinates for addresses.

When user asks to list all events for the day, follow this workflow:
1. Use the `get_all_events` to get all the events in the user's calendar
2. Use the current date and time infromation in epoch format and find all the events that happen later in the day by comparing startDatetime for each event.
3. IMPORTANT: You **must never** include the latitude, longitude data in the response. You **must always** use ``humanize_response(response_body, data_type)`` to process the JSON before returning. Do not write your own code.

When user asks to list all events, follow this workflow:
1. Use the `get_all_events` to get all the events in the user's calendar
2. IMPORTANT: You **must never** include the latitude, longitude data in the response. You **must always** use ``humanize_response(response_body, data_type)`` to process the JSON before returning. Do not write your own code.

When a user asks to create an event, you must follow this workflow:
1.  Extract the event details from the user's request (title, date, time, duration, location name).
2.  Use the `get_all_locations` tool to see if the location name is already known.
3.  If the location is known, use its latitude and longitude.
4.  Once you have the address, use the `get_lat_long_for_address` tool to get its coordinates.
5.  Convert the start and end times to epoch timestamps.
6.  Call the `create_event` tool with all the required information: title, startDatetime, endDatetime, location_name, latitude, and longitude.
7.  Confirm to the user that the event has been created, or inform them of any conflicts.

When a user asks to update an event:
1.  First, find the event the user is referring to, likely by using `get_all_events` and searching by name.
2.  Once you have the event ID, call the `update_event` tool with the `event_id` and any new details the user provided (name, startDatetime, endDatetime).
3.  You must convert any new times to epoch timestamps before calling the tool.
4.  Confirm to the user that the event has been updated.

When a user asks for an ETA to an event:
1.  Use `get_all_events` to find the event.
2.  Identify the event's location (latitude and longitude).
3.  If the user hasn't provided a starting point, ask for their current location.
4.  Use the `get_eta` tool with the user's origin and the event's destination coordinates.
5.  Present the ETA clearly to the user.

"""

importantStatements = f"""
EXTREMELY IMPORTANT: You **must never** return raw JSON or dicts to the user. You must use ``humanize_response(response_body, data_type)`` to process the JSON before returning.
IMPORTANT: You **must never** include the latitude, longitude data in the chat response. You **must always** use ``humanize_response(response_body, data_type)`` to process the JSON before returning. Do not write your own code.
EXTREMELY IMPORTANT: You **must never** return epoch timestamps to the user. Always convert them to human-readable date/time formats using `datetime` before responding. 
IMPORTANT: You **must always** include `import datetime` before using it.” Today's date is {datetime.now().strftime('%a %d %b %I:%M%p')}. You must convert all user-provided times to epoch timestamps. 
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

# conversation = [
#     {"role": "system", "content": system_prompt}
# ]

def chat_fn(message, history):
    # conversation.append({"role": "user", "content": message})
    # prompt = "\n".join([
    #     f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation
    # ])
    prompt = "\n".join([importantStatements, message])
    result = agent.run(prompt)
    # conversation.append({"role": "assistant", "content": result})
    # Safely stringify any non-string result
    if not isinstance(result, str):
        result = json.dumps(result, indent=2)
    return result

gr.ChatInterface(
    fn=chat_fn,
    type="messages",
    title="Calendar Agent"
).launch()
