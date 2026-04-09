# Ollama Local LLM Setup Guide

This project uses **Ollama** to run local LLMs for email processing. No OpenAI API key required!

## Quick Start

### Step 1: Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
1. Download from [ollama.com/download](https://ollama.com/download)
2. Run the installer

**Verify installation:**
```bash
ollama --version
```

### Step 2: Pull a Model

Download a model (recommended: **llama3.2** - fast, good quality):

```bash
ollama pull llama3.2
```

Other options:
- `ollama pull llama3` - Llama 3 (larger, better quality)
- `ollama pull mistral` - Mistral 7B
- `ollama pull phi3` - Microsoft Phi-3 (small, fast)

### Step 3: Start Ollama Server

Ollama runs as a background service. Make sure it's running:

```bash
ollama serve
```

Or on Windows/Mac, it starts automatically.

**Test the server:**
```bash
ollama run llama3.2
> Hello, are you working?
```

Press `Ctrl+D` to exit.

### Step 4: Configure the Agent

Edit `config/.env`:

```bash
cp config/.env.example config/.env
```

```env
# Local LLM Configuration (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Agent Configuration
MAX_EMAILS=5
TEMPERATURE=0.3
```

### Step 5: Run the Agent

```bash
python scripts/run_agent.py
```

---

## Configuration Options

### Available Models

| Model | Size | Speed | Quality | Command |
|-------|------|-------|---------|---------|
| llama3.2 | 3B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | `ollama pull llama3.2` |
| phi3 | 3.8B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | `ollama pull phi3` |
| mistral | 7B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | `ollama pull mistral` |
| llama3 | 8B | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | `ollama pull llama3` |
| gemma2 | 9B | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | `ollama pull gemma2` |

**For email tasks, llama3.2 is recommended** - it's fast and produces good quality responses.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama server URL | http://localhost:11434 |
| `OLLAMA_MODEL` | Model name to use | llama3.2 |
| `MAX_EMAILS` | Max emails to process | 5 |
| `TEMPERATURE` | Response creativity (0-1) | 0.3 |

---

## Troubleshooting

### Error: "Connection refused" or "Failed to connect"

**Solution:** Ollama server is not running.

```bash
# Start the server
ollama serve

# Or on macOS/Windows, restart Ollama app
```

### Error: "Model not found"

**Solution:** Pull the model first.

```bash
ollama pull llama3.2
```

### Error: "Model not supported" or timeout

**Solution:** Try a smaller/faster model.

```bash
ollama pull phi3
# Then update config/.env: OLLAMA_MODEL=phi3
```

### Slow responses

**Solution:** Use a smaller model or check system resources.

```bash
# Check available models
ollama list

# Use a smaller model
ollama pull llama3.2
```

### GPU not being used (slow inference)

Ollama automatically uses GPU if available. Check:

```bash
ollama ps
```

If GPU is not detected, you may need NVIDIA drivers or ROCm for AMD.

---

## Advanced: Custom Model

Create a custom model with specific parameters:

**1. Create a Modelfile:**

```dockerfile
FROM llama3.2

SYSTEM You are a professional email assistant. Be concise, helpful, and professional.

PARAMETER temperature 0.3
PARAMETER num_ctx 4096
```

**2. Build and run:**

```bash
ollama create email-assistant -f Modelfile
ollama run email-assistant
```

**3. Update config/.env:**

```env
OLLAMA_MODEL=email-assistant
```

---

## System Requirements

| Model | RAM Required | Disk Space |
|-------|-------------|------------|
| llama3.2 | 4GB | 2GB |
| phi3 | 4GB | 2.5GB |
| mistral | 8GB | 4.5GB |
| llama3 | 8GB | 4.7GB |

**Minimum:** 4GB RAM, 5GB disk space  
**Recommended:** 8GB+ RAM, SSD

---

## Useful Commands

```bash
# List downloaded models
ollama list

# Remove a model
ollama rm llama3.2

# Show model info
ollama show llama3.2

# Run with custom parameters
ollama run llama3.2 --verbose

# Check running models
ollama ps

# Stop all models
ollama stop llama3.2
```

---

## Need Help?

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Ollama Model Library](https://ollama.com/library)
- [LangChain Ollama Integration](https://python.langchain.com/docs/integrations/chat/ollama/)
