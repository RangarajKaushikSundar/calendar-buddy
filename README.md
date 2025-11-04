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

## Setup

Follow these steps to set up and run the project on your local machine.

### Prerequisites

-   Node.js (v18.x or later)
-   Python (v3.12 works for googlemaps and gradio, later versions seem to have compat issues)
-   `npm` (comes with Node.js)
-   `pip` (comes with Python)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <repository-name>
```

### 2. Set Up Environment Variables

The agent requires API keys for Google Maps and Hugging Face.

1.  Create a `.env` file in the project's root directory:
    ```bash
    touch .env
    ```

2.  Add your API keys to the `.env` file:
    ```
    GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY"
    HF_API_TOKEN="YOUR_HUGGINGFACE_API_TOKEN"
    ```

### 3. Install Dependencies

You'll need to install dependencies for both the Node.js service and the Python agent.

#### Calendar Service (Node.js)

```bash
cd calendar-service
npm install
cd ..
```

#### AI Agent (Python)

It's recommended to use a virtual environment.

```bash
# Navigate to the agent directory
cd smolagents

# Create and activate a virtual environment
python3.12 -m venv venv_stable
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install Python packages
pip install smolagents gradio requests python-dotenv googlemaps
```

## Running the Application

You need to run both the backend service and the AI agent simultaneously.

### Step 1: Start the Calendar Service

Open a terminal and run the following commands:

```bash
cd calendar-service
npm start
```

The calendar service will be running on `http://localhost:3000`.

### Step 2: Start the AI Agent

Open a second terminal and run the following commands:

```bash
cd smolagents
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

python main.py
```

The Gradio UI will launch, and the console will display the local URL (e.g., `http://127.0.0.1:7860`).

## Usage

1.  Open the Gradio URL (e.g., `http://127.0.0.1:7860`) in your web browser.
2.  Start interacting with your calendar assistant!

**Example Prompts:**
-   "What's on my calendar for today?"
-   "Book a 1-hour meeting with the design team at the office tomorrow at 11 AM."
-   "What's the ETA for my next meeting? I'm at home."
-   "Delete the 'Team Standup' event."