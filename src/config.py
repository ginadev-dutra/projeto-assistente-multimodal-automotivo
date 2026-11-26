import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
DEFAULT_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')
PROVEDOR = os.getenv('PROVEDOR', 'groq').strip().lower()
