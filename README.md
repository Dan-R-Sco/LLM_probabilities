# LLM Word Probability Visualizer

Interactive web application that visualizes token-level probabilities from Google's Gemini 2.0 model via Vertex AI. Users enter a prompt and receive AI-generated text where each token is hoverable to reveal its probability and top-5 alternative tokens.

## Features

- Real-time text generation using Google's Gemini 2.0 Flash model
- Token-level probability visualization
- Interactive tooltips showing alternative token choices
- Clean, modern UI with responsive design

## Prerequisites

Before running this application, ensure you have:

- Python 3.8 or higher
- A Google Cloud Platform account
- Vertex AI API enabled for your project
- Google Cloud SDK (`gcloud`) installed

## Setup Instructions

### 1. Google Cloud Authentication

First, authenticate with Google Cloud and set your project:

```powershell
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
gcloud config set account YOUR_EMAIL@domain.com
```

Replace `YOUR_PROJECT_ID` with your actual Google Cloud project ID and `YOUR_EMAIL@domain.com` with your Google account email.

### 2. Enable Vertex AI API

Make sure the Vertex AI API is enabled for your project:
- Visit: `https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=YOUR_PROJECT_ID`
- Click "Enable" if not already enabled

### 3. Environment Configuration

Create a `.env` file in the project root directory with the following content:

```properties
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

Replace `your-project-id` with your actual Google Cloud project ID.

### 4. Install Dependencies

Activate the virtual environment and install required packages:

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
uv pip sync requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

If you don't have `uv` installed, you can use regular pip:

```powershell
pip install -r requirements.txt
```

## Running the Application

1. **Activate the virtual environment** (if not already activated):
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Start the FastAPI server**:
   ```powershell
   uvicorn main:app --reload
   ```

3. **Access the application**:
   - Open your browser and navigate to `http://127.0.0.1:8000`
   - The API documentation is available at `http://127.0.0.1:8000/docs`

## Usage

1. Enter a prompt in the text area (e.g., "Write a short story about a robot")
2. Click "Generate" or press Enter
3. Hover over any generated token to see:
   - The token's probability
   - Top 5 alternative tokens with their probabilities

## Troubleshooting

### "PERMISSION_DENIED" Errors

**Cause**: Wrong Google account or insufficient IAM permissions

**Solution**:
1. Check active account: `gcloud auth list`
2. Switch if needed: `gcloud config set account CORRECT_EMAIL`
3. Re-authenticate: `gcloud auth application-default login`

### "API has not been enabled" Errors

**Cause**: Vertex AI API not activated for your project

**Solution**: Enable the API at the link mentioned in the setup instructions above

### Project Mismatch

**Cause**: `.env` file has a different project than `gcloud config`

**Solution**: The application uses `.env` first, so update gcloud to match:
```powershell
gcloud config set project $(python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GOOGLE_CLOUD_PROJECT'))")
```

## Project Structure

```
llm-word-prob/
├── main.py              # FastAPI application and backend logic
├── static/
│   ├── script.js        # Frontend JavaScript
│   └── style.css        # Styling
├── templates/
│   └── index.html       # Main HTML template
├── .env                 # Environment configuration (create this)
├── pyproject.toml       # Project dependencies
├── requirements.txt     # Compiled dependencies
└── README.md           # This file
```

## Technology Stack

- **Backend**: FastAPI, Python 3.12
- **AI Model**: Google Gemini 2.0 Flash (via Vertex AI)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Templating**: Jinja2

## Development

To regenerate dependencies after modifying `pyproject.toml`:

```powershell
uv pip compile pyproject.toml -o requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
uv pip sync requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

## License

This project is for educational and demonstration purposes.
