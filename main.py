#.\.venv\Scripts
#gcloud auth application-default login
#uvicorn main:app --reload
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import math
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Using Vertex AI with Google Cloud CLI authentication
# Configuration priority:
# 1. Environment variables from .env file (GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION)
# 2. Fallback to gcloud config
# 
# Authentication: Run `gcloud auth application-default login` before starting

# Get project ID and location from environment or gcloud config
project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT')
location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')

if not project_id:
    print("⚠️  WARNING: GOOGLE_CLOUD_PROJECT not set in .env file. Attempting to get from gcloud...")
    import subprocess
    try:
        result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                              capture_output=True, text=True, check=True)
        project_id = result.stdout.strip()
        print(f"📋 Using project from gcloud: {project_id}")
    except:
        print("❌ ERROR: Could not determine project ID.")
        print("   Please either:")
        print("   1. Set GOOGLE_CLOUD_PROJECT in .env file, OR")
        print("   2. Run 'gcloud config set project YOUR_PROJECT_ID'")

# Initialize Vertex AI
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig
    
    if project_id:
        vertexai.init(project=project_id, location=location)
        print(f"✅ Vertex AI initialized")
        print(f"   Project: {project_id}")
        print(f"   Location: {location}")
    else:
        print("❌ ERROR: No project ID available. Vertex AI not initialized.")
except ImportError as e:
    print(f"❌ ERROR: Vertex AI library not installed: {e}")
    print("   Run: pip install google-cloud-aiplatform")
except Exception as e:
    print(f"❌ ERROR: Vertex AI initialization failed: {e}")
    print("   Make sure you're authenticated with:")
    print("   gcloud auth application-default login")


# Initialize FastAPI app
app = FastAPI()

# Mount static files directory to serve CSS and JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates for rendering HTML
templates = Jinja2Templates(directory="templates")

# Pydantic model for the request body to ensure type safety
# Pydantic model for the request body to ensure type safety
class PromptRequest(BaseModel):
    prompt: str

# --- FastAPI Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serves the main HTML page.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_text(request: PromptRequest):
    """
    Generates text using the Gemini model and returns token probabilities.
    This endpoint handles the core logic of the application.
    """
    # Check if Vertex AI was initialized
    if not project_id:
        raise HTTPException(
            status_code=500, 
            detail="Vertex AI not configured. Please set GOOGLE_CLOUD_PROJECT in .env file or run 'gcloud config set project YOUR_PROJECT_ID'"
        )
    
    try:
        # Initialize the generative model using Vertex AI
        model = GenerativeModel('gemini-2.0-flash-exp')

        # Generate content with log probabilities
        # The SDK supports response_logprobs and logprobs parameters
        generation_config = GenerationConfig(
            temperature=0.9,
            #top_p=1.0,
            top_k=32,
            candidate_count=1,
            max_output_tokens=2048,
            response_logprobs=True,  # Enable returning log probabilities
            logprobs=5,  # Return top 5 alternative tokens
        )
        
        print(f"🔧 Generating content with model: gemini-2.0-flash-exp")
        print(f"🔧 Config: response_logprobs=True, logprobs=5")
        
        response = model.generate_content(
            request.prompt,
            generation_config=generation_config
        )
    except Exception as e:
        error_message = str(e)
        if "PERMISSION_DENIED" in error_message:
            raise HTTPException(
                status_code=403,
                detail=f"Authentication error. Please ensure:\n1. You're logged in: gcloud auth application-default login\n2. Using correct account: gcloud config set account YOUR_EMAIL\n3. Project is correct: {project_id}\n\nError: {error_message}"
            )
        elif "API has not been enabled" in error_message:
            raise HTTPException(
                status_code=503,
                detail=f"Vertex AI API not enabled for project {project_id}. Enable it at: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={project_id}"
            )
        else:
            raise HTTPException(status_code=500, detail=f"Error generating content: {error_message}")

    # --- Process the response ---
    if not response.candidates:
        raise HTTPException(status_code=500, detail="No content generated by the model.")

    candidate = response.candidates[0]
    
    # Debug: Check what we got back
    print(f"🔍 Candidate has logprobs_result attribute: {hasattr(candidate, 'logprobs_result')}")
    if hasattr(candidate, 'logprobs_result'):
        print(f"🔍 logprobs_result value: {candidate.logprobs_result}")
        print(f"🔍 logprobs_result is None: {candidate.logprobs_result is None}")
    
    # Check for logprobs_result (correct attribute name for Vertex AI)
    if not hasattr(candidate, 'logprobs_result') or not candidate.logprobs_result:
        # Fallback: No logprobs returned
        text = ""
        if candidate.content and candidate.content.parts:
            text = candidate.content.parts[0].text
        print(f"⚠️  WARNING: No logprobs_result returned. Returning text only.")
        return JSONResponse(content={"response": [], "text": text})

    # Extract logprobs using the correct structure
    logprobs_result = candidate.logprobs_result
    
    # Get the generated text
    generated_text = candidate.content.parts[0].text if candidate.content and candidate.content.parts else ""

    # Build response data from logprobs_result
    response_data = []
    chosen_candidates = logprobs_result.chosen_candidates
    top_candidates = logprobs_result.top_candidates
    
    print(f"📊 Processing {len(chosen_candidates)} tokens with logprobs")
    
    for i, chosen_candidate in enumerate(chosen_candidates):
        token_str = chosen_candidate.token
        log_prob = chosen_candidate.log_probability
        # Convert log probability to probability
        probability = math.exp(log_prob)
        
        # Get top 5 alternative tokens for this position
        top_5_tokens = {}
        if i < len(top_candidates):
            top_alternatives = top_candidates[i].candidates
            # Get alternatives (excluding the chosen token)
            for alt_token_info in top_alternatives[:5]:  # Get top 5
                alt_token = alt_token_info.token
                alt_log_prob = alt_token_info.log_probability
                top_5_tokens[alt_token] = math.exp(alt_log_prob)
        
        response_data.append({
            "token": token_str,
            "probability": probability,
            "top_5": top_5_tokens
        })

    print(f"📊 Generated {len(response_data)} tokens with probabilities")
    return JSONResponse(content={"response": response_data, "text": generated_text})

# --- Main execution ---
if __name__ == "__main__":
    # This allows running the app with `python main.py`
    # For development, it's recommended to use `uvicorn main:app --reload`
    uvicorn.run(app, host="0.0.0.0", port=8000)

""" TODOS
Potentially Available Outputs:
1. Usage Metadata (response.usage_metadata)
prompt_token_count - Number of tokens in your input
candidates_token_count - Number of tokens generated
total_token_count - Total tokens used (for billing)
Useful for: Cost tracking, performance optimization
2. Finish Reason (candidate.finish_reason)
STOP - Normal completion
MAX_TOKENS - Hit token limit
SAFETY - Blocked by safety filters
RECITATION - Blocked due to recitation
Useful for: Understanding why generation stopped
3. Safety Ratings (candidate.safety_ratings)
Categories: HARM_CATEGORY_HARASSMENT, HATE_SPEECH, SEXUALLY_EXPLICIT, DANGEROUS_CONTENT
Probability ratings: NEGLIGIBLE, LOW, MEDIUM, HIGH
Useful for: Content moderation, compliance
4. Citation Metadata (candidate.citation_metadata)
Citations to sources if model used web grounding
Useful for: Fact-checking, attribution
5. Grounding Metadata (candidate.grounding_metadata)
Information about web search results used
Grounding scores and sources
Useful for: Understanding factual basis
    
    # Check interesting metadata
    if hasattr(response, 'usage_metadata'):
        print(f"📊 Usage metadata: {response.usage_metadata}")
    if hasattr(candidate, 'finish_reason'):
        print(f"🏁 Finish reason: {candidate.finish_reason}")
    if hasattr(candidate, 'safety_ratings'):
        print(f"🛡️  Safety ratings: {candidate.safety_ratings}")
    if hasattr(candidate, 'citation_metadata'):
        print(f"📚 Citation metadata: {candidate.citation_metadata}")
    if hasattr(candidate, 'grounding_metadata'):
        print(f"🔗 Grounding metadata: {candidate.grounding_metadata}")"""