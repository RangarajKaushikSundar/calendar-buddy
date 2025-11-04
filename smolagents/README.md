## Setup

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
