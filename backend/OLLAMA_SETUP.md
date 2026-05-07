# Ollama Integration Guide

This project now supports using local LLMs via Ollama as an alternative or fallback to Google Gemini.

## Setup

1. **Install Ollama**: Download and install Ollama from [ollama.com](https://ollama.com).
2. **Pull the Model**: Run the following command to download the Gemma 3:4b model:
   ```bash
   ollama pull gemma3:4b
   ```
3. **Configuration**:
   Update your `.env` file with the following variables:
   - `AI_PROVIDER`: Set to `"ollama"` to use Ollama as the primary provider, or `"gemini"` to use Gemini.
   - `OLLAMA_BASE_URL`: The URL where Ollama is running (default: `http://localhost:11434`).
   - `OLLAMA_MODEL`: The model name (default: `gemma3:4b`).

## How it Works

The `ai_service.py` implements a fallback mechanism:
- If `AI_PROVIDER` is set to `gemini` and the Gemini API call fails, the system will automatically attempt to use the Ollama provider for that specific request.
- If `AI_PROVIDER` is set to `ollama` and it fails, it will attempt to fallback to Gemini.

This ensures high availability of AI features even if one provider is experiencing downtime or rate limits.
