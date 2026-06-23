# Ollama + qwen2-vl:4b Setup for Naukri AI Bot

Your bot now uses **Ollama with qwen2-vl:4b as the primary AI backend**, with Gemini as fallback to avoid API rate limits.

## ✅ Quick Setup

### 1. Install & Run Ollama

**macOS:**
```bash
brew install ollama
ollama serve
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

**Windows:**
- Download from https://ollama.ai
- Run the installer

### 2. Pull the qwen2-vl:4b Model

In a new terminal:
```bash
ollama pull qwen2-vl:4b
```

This downloads the 4B vision model (~3GB). Wait for completion.

### 3. Verify Ollama is Running

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2-vl:4b",
  "prompt": "Hello",
  "stream": false
}'
```

You should get a JSON response with generated text.

### 4. Run the Naukri Bot

```bash
cd /Users/koushik/Documents/naukri_ai_bot_automatic_job_apply
source venv/bin/activate  # or create it: python3 -m venv venv && source venv/bin/activate
python3 src/bot.py
```

## 🔧 Configuration (src/conf.py)

```python
# Ollama is PRIMARY
USE_OLLAMA_FIRST = True
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2-vl:4b"

# Gemini is FALLBACK
API_KEY = "your_gemini_api_key"  # only used if Ollama fails
MODEL = "gemini-2.5-flash"
```

## 📊 What Happens During Runtime

1. **Bot receives question** → Checks cache first
2. **Cache miss?** → Tries Ollama (qwen2-vl:4b) on localhost
3. **Ollama fails/timeout?** → Falls back to Gemini API
4. **All backends fail?** → Skips job (rate limit safe)

## 🎯 Benefits

- ✅ No API rate limits (Ollama runs locally)
- ✅ Faster responses (no network latency to Google)
- ✅ Privacy (questions never leave your machine)
- ✅ Fallback to Gemini if needed
- ✅ Cached answers reused across sessions

## ⚡ Performance Tips

**Faster Answers:**
```bash
# Run Ollama with GPU acceleration (if available)
CUDA_VISIBLE_DEVICES=0 ollama serve
```

**Reduce Model Size:**
Change to lighter model in conf.py:
```python
OLLAMA_MODEL = "qwen:1b"  # 1B version (faster, less accurate)
```

**Check System Stats During Runtime:**
```bash
ollama list  # See all models
ollama show qwen2-vl:4b  # Model details
```

## 🚨 Troubleshooting

**Error: "Connection refused"**
- Ollama not running → Run `ollama serve` in a terminal

**Error: "Model not found"**
- Pull the model: `ollama pull qwen2-vl:4b`

**Slow Responses**
- Reduce model size or wait for GPU support
- Increase timeout in bot.py if needed (currently 120s)

**Want to Switch Back to Gemini?**
```python
USE_OLLAMA_FIRST = False  # in conf.py
```

## 📈 Monitoring

After each run, check statistics:
```
📊 AI Backend Statistics:
   Total Questions: 45
   Cached Answers: 30
   Generated Answers: 15
   Ollama Used: 12
   Gemini Used: 3
   Cache Hit Rate: 66.7%
```

High cache hit rate = fewer API calls = faster runs.

---

**Questions?** Check the logs: `tail -f logs/bot.log`
