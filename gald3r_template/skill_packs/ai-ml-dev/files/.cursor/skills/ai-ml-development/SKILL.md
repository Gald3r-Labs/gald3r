---
name: ai-ml-development
description: AI/ML training through deployment — fine-tuning, RLHF, multimodal systems, RAG, memory, MLOps, and tool integration.
version: 1.0.0
---

# AI/ML Development Skill

Comprehensive reference for AI/ML model training, development, and production deployment. This skill supports three specialized agents:

- **ai-model-trainer**: Training, fine-tuning, RLHF, research integration
- **ai-model-developer**: Tool integration, multi-modal, memory, production-ready
- **mlops-engineer**: Hosting, deployment, inference optimization

## Quick Reference

### Training Methods

| Method | Use Case | Data Needed | Compute |
|--------|----------|-------------|---------|
| Full Fine-tuning | Domain adaptation | 10k-100k+ examples | High (multi-GPU) |
| LoRA/QLoRA | Efficient fine-tuning | 1k-50k examples | Medium (single GPU) |
| Instruction Tuning | Task following | 1k-10k instructions | Medium |
| RLHF/DPO | Alignment | 1k-10k preferences | High |
| Few-shot | Quick adaptation | 5-50 examples | None (inference only) |

### Model Serving Options

| Platform | Best For | Cost Model | Latency |
|----------|----------|------------|---------|
| HuggingFace Endpoints | Easy deployment | Per-hour | Medium |
| vLLM (self-hosted) | High throughput | Infrastructure | Low |
| AWS SageMaker | Enterprise | Per-hour + requests | Medium |
| Replicate/Modal | Serverless | Per-second | Variable |
| OpenAI/Anthropic API | No infrastructure | Per-token | Low |

### Memory Architectures

| Type | Persistence | Use Case |
|------|-------------|----------|
| Context Window | Session | Current conversation |
| RAG (Vector DB) | Permanent | Knowledge retrieval |
| Conversation Memory | Session/Permanent | Chat history |
| Episodic Memory | Permanent | User preferences |

## Training Guide

### Fine-Tuning Decision Tree

```
Is your task well-defined?
├── Yes: Do you have labeled data?
│   ├── Yes (>10k): Full fine-tuning or LoRA
│   ├── Yes (1k-10k): LoRA/QLoRA
│   └── No: Generate synthetic data or use few-shot
└── No: Start with prompting, iterate to fine-tuning
```

### LoRA Configuration Guide

```python
# Recommended LoRA configs by model size

# 7B-13B models
lora_config_small = {
    "r": 16,           # Rank
    "lora_alpha": 32,  # Alpha (usually 2x rank)
    "target_modules": ["q_proj", "v_proj"],
    "lora_dropout": 0.05,
    "bias": "none",
}

# 30B-70B models
lora_config_large = {
    "r": 64,
    "lora_alpha": 128,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", 
                       "gate_proj", "up_proj", "down_proj"],
    "lora_dropout": 0.1,
    "bias": "none",
}

# QLoRA (4-bit quantization)
qlora_config = {
    "load_in_4bit": True,
    "bnb_4bit_compute_dtype": "float16",
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_use_double_quant": True,
}
```

### RLHF vs DPO Comparison

| Aspect | RLHF (PPO) | DPO |
|--------|------------|-----|
| Complexity | High (reward model + PPO) | Low (direct optimization) |
| Stability | Can be unstable | More stable |
| Data | Preferences → Reward model | Direct preferences |
| Compute | 2-3x more | Standard fine-tuning |
| Results | State-of-the-art | Comparable |

**Recommendation**: Start with DPO, use RLHF for maximum control.

## Tool Integration

### Function Calling Schema

```json
{
  "name": "search_web",
  "description": "Search the web for current information",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query"
      },
      "num_results": {
        "type": "integer",
        "description": "Number of results (1-10)",
        "default": 5
      }
    },
    "required": ["query"]
  }
}
```

### Tool Integration Patterns

```python
# Pattern 1: Simple tool executor
class ToolExecutor:
    def __init__(self):
        self.tools = {
            "search": self.search,
            "calculate": self.calculate,
            "code_run": self.code_run,
        }
    
    async def execute(self, tool_call: dict) -> str:
        tool_name = tool_call["name"]
        args = tool_call["arguments"]
        
        if tool_name not in self.tools:
            return f"Unknown tool: {tool_name}"
        
        try:
            result = await self.tools[tool_name](**args)
            return json.dumps(result)
        except Exception as e:
            return f"Error: {str(e)}"

# Pattern 2: ReAct-style agent loop
async def agent_loop(query: str, max_iterations: int = 10):
    messages = [{"role": "user", "content": query}]
    
    for i in range(max_iterations):
        response = await llm.chat(messages, tools=TOOLS)
        
        if response.tool_calls:
            # Execute tools
            for tool_call in response.tool_calls:
                result = await executor.execute(tool_call)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            # Final response
            return response.content
    
    return "Max iterations reached"
```

## Memory Systems

### RAG Implementation

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. Document Processing
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)
chunks = text_splitter.split_documents(documents)

# 2. Embedding & Storage
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# 3. Retrieval
retriever = vectorstore.as_retriever(
    search_type="mmr",  # Maximum Marginal Relevance
    search_kwargs={"k": 5, "fetch_k": 20}
)

# 4. Query with context
def query_with_rag(question: str) -> str:
    relevant_docs = retriever.get_relevant_documents(question)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    
    prompt = f"""Use the following context to answer the question.

Context:
{context}

Question: {question}

Answer:"""
    
    return llm.generate(prompt)
```

### Conversation Memory

```python
class ConversationMemory:
    def __init__(self, max_tokens: int = 4000):
        self.messages = []
        self.max_tokens = max_tokens
    
    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self._trim_to_limit()
    
    def _trim_to_limit(self):
        """Remove oldest messages to stay under token limit"""
        while self._count_tokens() > self.max_tokens:
            # Keep system message, remove oldest user/assistant
            if len(self.messages) > 1:
                self.messages.pop(1)
            else:
                break
    
    def get_context(self) -> list:
        return self.messages.copy()
    
    def summarize_and_compress(self):
        """Summarize old messages to save context"""
        if len(self.messages) > 10:
            old_messages = self.messages[1:-4]  # Keep recent 4
            summary = llm.generate(f"Summarize: {old_messages}")
            self.messages = [
                self.messages[0],  # System
                {"role": "system", "content": f"Previous context: {summary}"},
                *self.messages[-4:]  # Recent messages
            ]
```

## MLOps & Deployment

### HuggingFace Deployment

```python
# Upload model to Hub
from huggingface_hub import HfApi

api = HfApi()
api.upload_folder(
    folder_path="./model",
    repo_id="your-org/model-name",
    repo_type="model"
)

# Create Inference Endpoint (via API)
import requests

endpoint = requests.post(
    "https://api.endpoints.huggingface.cloud/v2/endpoint",
    headers={"Authorization": f"Bearer {HF_TOKEN}"},
    json={
        "name": "my-model-endpoint",
        "repository": "your-org/model-name",
        "framework": "pytorch",
        "task": "text-generation",
        "instance_size": "medium",
        "instance_type": "g5.xlarge",
        "min_replica": 0,
        "max_replica": 2
    }
)
```

### vLLM Serving

```bash
# Install
pip install vllm

# Serve model
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3-8B-Instruct \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 8192

# With quantization
python -m vllm.entrypoints.openai.api_server \
    --model TheBloke/Llama-3-8B-Instruct-AWQ \
    --quantization awq \
    --dtype half
```

### Model Optimization Checklist

```
□ Quantization
  □ INT8 (2x memory reduction, ~5% quality loss)
  □ INT4/AWQ/GPTQ (4x reduction, ~10% quality loss)
  □ GGUF for CPU inference

□ Inference Optimization
  □ KV-cache optimization
  □ Continuous batching
  □ Speculative decoding (if supported)
  □ Flash Attention 2

□ Serving Configuration
  □ Appropriate batch size
  □ Request queuing
  □ Timeout handling
  □ Health checks

□ Monitoring
  □ Latency (P50, P95, P99)
  □ Throughput (tokens/sec)
  □ Error rate
  □ GPU utilization
  □ Memory usage
```

## Evaluation

### Common Benchmarks

| Benchmark | Measures | Good Score |
|-----------|----------|------------|
| MMLU | General knowledge | >70% |
| HumanEval | Code generation | >50% |
| GSM8K | Math reasoning | >70% |
| TruthfulQA | Factual accuracy | >50% |
| MT-Bench | Instruction following | >7/10 |

### Custom Evaluation

```python
def evaluate_model(model, test_cases: list) -> dict:
    results = {
        "accuracy": 0,
        "latency_p50": 0,
        "latency_p95": 0,
        "errors": []
    }
    
    latencies = []
    correct = 0
    
    for case in test_cases:
        start = time.time()
        try:
            output = model.generate(case["input"])
            latency = time.time() - start
            latencies.append(latency)
            
            if evaluate_output(output, case["expected"]):
                correct += 1
        except Exception as e:
            results["errors"].append(str(e))
    
    results["accuracy"] = correct / len(test_cases)
    results["latency_p50"] = np.percentile(latencies, 50)
    results["latency_p95"] = np.percentile(latencies, 95)
    
    return results
```

## Cost Optimization

### Training Cost Estimation

| Model Size | Full Fine-tune | LoRA | QLoRA |
|------------|----------------|------|-------|
| 7B | $50-200 | $10-50 | $5-20 |
| 13B | $100-500 | $20-100 | $10-50 |
| 70B | $500-2000 | $100-500 | $50-200 |

*Costs are approximate, based on cloud GPU pricing*

### Inference Cost Comparison

| Option | Cost/1M tokens | Best For |
|--------|----------------|----------|
| OpenAI GPT-4 | $30-60 | Low volume, high quality |
| OpenAI GPT-3.5 | $0.50-2 | Medium volume |
| Claude 3 Opus | $15-75 | Complex tasks |
| Self-hosted 7B | $0.10-0.50 | High volume |
| Self-hosted 70B | $1-5 | High volume, high quality |

## Resources

### Reference Documents
- `reference/fine_tuning_guide.md` - Detailed fine-tuning procedures
- `reference/rlhf_implementation.md` - RLHF/DPO implementation
- `reference/deployment_checklist.md` - Production deployment guide
- `reference/cost_optimization.md` - Cost reduction strategies

### Templates
- `templates/training_config.yaml` - Training configuration template
- `templates/evaluation_suite.py` - Evaluation script template
- `templates/deployment_manifest.yaml` - K8s deployment template

### External Resources
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [vLLM Documentation](https://docs.vllm.ai)
- [LangChain](https://python.langchain.com)
- [LlamaIndex](https://docs.llamaindex.ai)

---
*This skill supports: ai-model-trainer, ai-model-developer, mlops-engineer agents*
