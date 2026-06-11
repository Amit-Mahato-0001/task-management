import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_client():
    return supabase


def get_user_from_token(token: str):
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {token}",
        }
        response = requests.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)
        if response.status_code != 200:
            print(f"Auth error: {response.status_code} - {response.text}")
            return None
        return response.json()
    except Exception as e:
        print(f"Token validation error: {str(e)}")
        return None
