import os, requests, polyline

from dotenv import load_dotenv
load_dotenv()

GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")


def _ck(key):
    if not key: raise RuntimeError("Missing GOOGLE_API_KEY. Add it to .env")

    