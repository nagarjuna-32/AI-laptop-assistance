import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

WAKE_WORD = "hey arjun"

# OPENAI_API_KEY should be provided via environment variable (recommended)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")




