"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class."""

    # Local LLM (Ollama)
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')

    # Gmail
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    CREDENTIALS_FILE = 'credentials.json'
    TOKEN_FILE = 'token.json'

    # Agent
    MAX_EMAILS = int(os.getenv('MAX_EMAILS', '5'))
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.3'))

    @classmethod
    def validate(cls):
        """Validate configuration."""
        # Check if Ollama is configured
        if not cls.OLLAMA_MODEL:
            raise ValueError("OLLAMA_MODEL not set in environment")

        print(f"Using local LLM: {cls.OLLAMA_MODEL}")
        print(f"Ollama server: {cls.OLLAMA_BASE_URL}")
