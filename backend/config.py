import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Security & Auth
SECRET_KEY = os.getenv("SECRET_KEY", "voice_ai_secret_super_secure_key_2026_xyz_789")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'voice_call.db'}")

# AI API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Audio Pipeline Settings
DEFAULT_SAMPLE_RATE = 16000
SILENCE_DURATION_MS = 600
MIN_AUDIO_DURATION_SEC = 0.5
MAX_AUDIO_DURATION_SEC = 25.0
