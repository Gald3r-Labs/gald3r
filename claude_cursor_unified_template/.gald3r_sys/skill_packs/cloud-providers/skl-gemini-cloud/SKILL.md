---
name: skl-gemini-cloud
description: Google Vertex AI & Gemini Cloud ΓÇö Gemini API, Vertex AI Model Garden, Cloud Run deployment, GCP setup, grounding with Google Search, cost management.
skill_group: "cloud-providers"
skill_category: "Cloud Provider Integration"
---

# Google Vertex AI & Gemini Cloud

Google's AI/ML cloud platform. Gemini API for direct LLM access; Vertex AI for MLOps, fine-tuning, and Model Garden.

## Prerequisites

- Google Cloud account: https://console.cloud.google.com/
- `gcloud` CLI: https://cloud.google.com/sdk/docs/install
- Auth: `gcloud auth login && gcloud auth application-default login`
- Enable APIs:
  ```bash
  gcloud services enable aiplatform.googleapis.com
  gcloud services enable run.googleapis.com
  ```

## Operation: GEMINI-API

Direct Gemini API via Google AI Studio (no Vertex needed).

```python
# pip install google-generativeai
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
# API key from: https://aistudio.google.com/app/apikey

model = genai.GenerativeModel("gemini-2.0-flash")

# Text generation
response = model.generate_content("Explain quantum entanglement simply")
print(response.text)

# Chat (multi-turn)
chat = model.start_chat()
response = chat.send_message("What is 2+2?")
response2 = chat.send_message("Multiply that by 3")

# With system instruction
model = genai.GenerativeModel(
    "gemini-2.0-flash",
    system_instruction="You are a concise technical assistant."
)

# With grounding (Google Search)
from google.generativeai.types import Tool, GoogleSearchRetrieval
model_with_search = genai.GenerativeModel(
    "gemini-2.0-flash",
    tools=[Tool(google_search_retrieval=GoogleSearchRetrieval())]
)
response = model_with_search.generate_content("Latest news about AI regulation in 2026")
```

**Safety settings:**
```python
from google.generativeai.types import HarmCategory, HarmBlockThreshold

model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content(
    "Your prompt here",
    safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    }
)
# Thresholds: BLOCK_NONE | BLOCK_ONLY_HIGH | BLOCK_MEDIUM_AND_ABOVE | BLOCK_LOW_AND_ABOVE
```

**Token counting (before sending large prompts):**
```python
# Count tokens without calling generate_content (billing awareness)
result = model.count_tokens("Your long document or prompt here...")
print(f"Input tokens: {result.total_tokens}")

# Count multimodal (image + text)
import PIL.Image
img = PIL.Image.open("diagram.png")
result = model.count_tokens(["Describe this image:", img])
print(f"Total tokens: {result.total_tokens}")
```

**Gemini models (2026):**
| Model | Context | Best For |
|-------|---------|---------|
| gemini-2.0-flash | 1M tokens | Fast, cost-efficient |
| gemini-2.0-pro | 2M tokens | Complex reasoning |
| gemini-1.5-flash | 1M tokens | Multimodal, cheap |

## Operation: VERTEX-AI

Vertex AI for production workloads and MLOps.

```python
# pip install google-cloud-aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project="my-project", location="us-central1")

model = GenerativeModel("gemini-2.0-flash-002")
response = model.generate_content("Your prompt here")
print(response.text)

# Batch predictions
from vertexai.batch_prediction import BatchPredictionJob
job = BatchPredictionJob.submit(
    source_model="gemini-2.0-flash-002",
    input_dataset="gs://my-bucket/prompts.jsonl",
    output_uri_prefix="gs://my-bucket/output/"
)
```

```bash
# gcloud equivalent
gcloud ai models list --region=us-central1
gcloud ai endpoints list --region=us-central1
```

## Operation: MODEL-GARDEN

Access to 100+ open models via Vertex AI.

```bash
# Deploy a model from Model Garden
gcloud ai endpoints create \
  --display-name=my-endpoint \
  --region=us-central1

# List deployable models
# Via console: console.cloud.google.com/vertex-ai/model-garden

# Deploy Llama model
gcloud ai models deploy MODEL_ID \
  --endpoint=ENDPOINT_ID \
  --region=us-central1 \
  --display-name=my-model
```

## Operation: CLOUD-RUN

Deploy containerized AI services serverlessly.

```bash
# Deploy from container
gcloud run deploy my-ai-service \
  --image us-docker.pkg.dev/cloudrun/container/hello \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY \
  --memory 2Gi --cpu 2

# Deploy from source (auto-builds with Buildpacks)
gcloud run deploy my-service --source . --region us-central1

# List services
gcloud run services list --region us-central1

# View logs
gcloud run services logs read my-ai-service --region us-central1 --tail 50
```

## Operation: GCP-SETUP

Essential GCP project setup.

```bash
# Create project
gcloud projects create my-project-id --name "My Project"
gcloud config set project my-project-id

# Enable billing (required for most services)
# console.cloud.google.com/billing/linkedaccount

# Create service account for gald3r/CI
gcloud iam service-accounts create gald3r-sa \
  --display-name "gald3r Service Account"

gcloud projects add-iam-policy-binding my-project-id \
  --member "serviceAccount:gald3r-sa@my-project-id.iam.gserviceaccount.com" \
  --role "roles/aiplatform.user"

# Download key (for server-side auth)
gcloud iam service-accounts keys create key.json \
  --iam-account gald3r-sa@my-project-id.iam.gserviceaccount.com
export GOOGLE_APPLICATION_CREDENTIALS=key.json
```

## Operation: GROUNDING

Connect Gemini to live Google Search data.

```python
# Via Vertex AI
from vertexai.generative_models import GenerativeModel, Tool, grounding

model = GenerativeModel("gemini-2.0-flash-002")
tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())
response = model.generate_content(
    "What are the latest developments in quantum computing?",
    tools=[tool]
)
# response.candidates[0].grounding_metadata contains search sources
```

**Vertex AI Search ΓÇö RAG Engine (document grounding):**
```python
# pip install google-cloud-discoveryengine
from google.cloud import discoveryengine_v1 as discoveryengine

client = discoveryengine.SearchServiceClient()
# Assumes you've created a datastore in Vertex AI Search console:
# console.cloud.google.com/gen-app-builder/data-stores

response = client.search(
    discoveryengine.SearchRequest(
        serving_config=f"projects/{PROJECT}/locations/global/collections/default_collection/dataStores/{DATASTORE_ID}/servingConfigs/default_serving_config",
        query="How does gald3r task management work?",
        page_size=5,
    )
)
for result in response.results:
    print(result.document.derived_struct_data["snippets"])
```

**Document AI integration (extract structure from PDFs/forms):**
```bash
# Enable Document AI API
gcloud services enable documentai.googleapis.com

# Process a document
gcloud beta documentai processors process-document \
  --processor=PROCESSOR_ID \
  --file-path=document.pdf \
  --location=us --output-gcs-uri=gs://my-bucket/output/
```
```python
from google.cloud import documentai

client = documentai.DocumentProcessorServiceClient()
with open("document.pdf", "rb") as f:
    raw = f.read()

result = client.process_document(
    request=documentai.ProcessRequest(
        name=f"projects/{PROJECT}/locations/us/processors/{PROCESSOR_ID}",
        raw_document=documentai.RawDocument(content=raw, mime_type="application/pdf")
    )
)
# result.document.text ΓÇö extracted full text
# result.document.entities ΓÇö structured fields (for form parsers)
```

## Operation: COST

Cost management for Gemini/Vertex.

```bash
# Set billing budget alert
gcloud billing budgets create \
  --billing-account BILLING_ACCOUNT_ID \
  --display-name "Gemini API Budget" \
  --budget-amount 50USD \
  --threshold-rule percent=0.8 \
  --threshold-rule percent=1.0

# View current billing
gcloud billing accounts list
gcloud beta billing accounts get-iam-policy ACCOUNT_ID

# Quotas (rate limits)
gcloud services quota list --service=aiplatform.googleapis.com --filter="name~gemini"
```

**Gemini pricing (approximate 2026):**
| Model | Input | Output |
|-------|-------|--------|
| gemini-2.0-flash | $0.075/M tokens | $0.30/M tokens |
| gemini-2.0-pro | $1.25/M tokens | $5.00/M tokens |

**Committed Use Discounts (CUD):**
```bash
# Vertex AI CUDs reduce costs for sustained AI API usage
# Purchase via: console.cloud.google.com/billing/commitments

# 1-year commitment: ~20% discount on Vertex AI Prediction spend
# 3-year commitment: ~35% discount

# Check available commitment types
gcloud beta billing commitments list --billing-account=$BILLING_ACCOUNT

# CUDs apply automatically to eligible Vertex AI usage (model serving, batch prediction)
# NOT applicable to: AI Studio direct API calls, Developer tier quotas
# Best for: production workloads with $500+/mo consistent Vertex AI spend
```
