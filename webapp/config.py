import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    DATA_FILE = os.getenv("DATA_FILE", "data/site_pages.json")
    CHATBOT_TITLE = os.getenv("CHATBOT_TITLE", "えびす堂 FAQチャット")

