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
