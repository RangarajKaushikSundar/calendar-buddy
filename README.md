# Calendar AI Assistant

This project is an intelligent calendar assistant that combines a Node.js backend for calendar management with a Python-based AI agent. The agent uses `smol-agent` to understand natural language, interacts with the calendar service's APIs, and leverages Google Maps for location-based functionalities like fetching ETAs and geocoding addresses. The user interface is built with Gradio, providing an intuitive chat-based experience.

## Features

- **Full Calendar Management**: Create, read, update, and delete calendar events through a robust API.
- **Conversational AI**: Interact with your calendar using natural language.
- **Google Maps Integration**: Automatically fetch latitude/longitude for new locations and get real-time ETAs for your events.
- **Interactive Web UI**: A clean and simple chat interface powered by Gradio.

## Project Structure

The project is organized into two main components:

-   `calendar-service/`: A Node.js application that exposes a REST API for CRUD operations on the calendar.
-   `smolagents/`: A Python application containing the AI agent, its tools, and the Gradio user interface.

## Usage
Note: Checkout the setup READMEs present within the Calendar service and smolagents folders.

1.  Open the Gradio URL (e.g., `http://127.0.0.1:7860`) in your web browser.
2.  Start interacting with your calendar assistant!

**Example Prompts:**
-   "What's on my calendar for today?"
-   "Book a 1-hour meeting with the design team at the office tomorrow at 11 AM."
-   "Delete the 'Team Standup' event."

## FEATURES WISHLIST
**Agent**
1. Conversational history: The code for this is commented out because the model is not sophesticated enough to handle large prompts
2. Fine tune responses: The CodeAgent is pretty good in creating code to chain the tools, but sporadically creates it's own code ignoring an existing tool. Unsure if this is due to model quality or type of agent
3. ETAs: Routes product is billed. Would love to explore this as the code as I struggled for an hour to get the API to work cross referencing [documentation](https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRoutes) after Gemini informed me that this is a paid feature.

**Calendar**
1. Persistence: There is no persistence for the calendar. Simple solution would be to use file persistence, a better way would be to use a database.

**Code**
1. Tests: I got Gemini to generate the tool tests for me and am not a huge fan of the quality of tests. This would be refactored with high priority
2. Python code: The agent code is already bloated with tool definitions. This should be broken out by responsibilities.

**Deployment**
There were a few solutions considered for this project.
1. AWS stack: Bedrock (agent) + Lambda (Calendar Service) + Dynamo (Calendar data)
2. OpenAI/Gemini + deployed service
3. Smolagents + Local server 