import os
import traceback
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from postgrest.exceptions import APIError
from supabase_client import get_supabase_client, get_user_from_token
from email_service import send_task_created_email, send_task_completed_email

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

supabase = get_supabase_client()  # This should use anon key by default

# Optional: create a separate admin client with service role key for checking table existence
service_key = os.getenv("SUPABASE_SERVICE_KEY")
if service_key:
    from supabase import create_client
    supabase_admin = create_client(os.getenv("SUPABASE_URL"), service_key)
else:
    supabase_admin = None  # fallback to regular client

# ------------------------------------------------------------
# Helper: ensure profile exists (as before, but with upsert fix)
# ------------------------------------------------------------
def ensure_profile(user):
    if not user:
        return None
    user_id = user.get("id")
    try:
        # Use eq filter (should work now if supabase client is correct)
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Profile query error: {e}")

    # Create/update profile
    metadata = user.get("user_metadata") or {}
    full_name = metadata.get("full_name") or metadata.get("name") or user.get("email")
    try:
        result = supabase.table("profiles").upsert(
            {"id": user_id, "email": user.get("email"), "full_name": full_name},
            on_conflict="id"
        ).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Profile upsert error: {e}")
        return None

# ------------------------------------------------------------
# Get user from token (same as before)
# ------------------------------------------------------------
def get_user_from_request():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    user = get_user_from_token(token)
    if user:
        ensure_profile(user)
    return user

# ------------------------------------------------------------
# Check if table exists - using admin client if available
# ------------------------------------------------------------
def table_exists(table_name: str) -> bool:
    client = supabase_admin if supabase_admin else supabase
    try:
        # Simple query to check existence; if table missing, exception is raised
        client.table(table_name).select("id").limit(1).execute()
        return True
    except Exception as e:
        # If error contains "relation" or "does not exist", table is missing
        error_str = str(e).lower()
        if "does not exist" in error_str or "relation" in error_str:
            return False
        # For other errors (like RLS), assume table exists but query failed
        # We'll still return True to avoid blocking, and let the actual query handle RLS
        print(f"table_exists unexpected error for {table_name}: {e}")
        return True  # optimistic

# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/debug-cors", methods=["GET", "OPTIONS"])
def debug_cors():
    return jsonify({"status": "cors ok"}), 200

@app.route("/debug/supabase", methods=["GET"])
def debug_supabase():
    profiles_exist = table_exists("profiles")
    tasks_exist = table_exists("tasks")
    return jsonify({
        "supabase_connected": True,
        "profiles_table_exists": profiles_exist,
        "tasks_table_exists": tasks_exist,
    })

# ---------- TASKS ----------
@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    user = get_user_from_request()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    profile_id = user.get("id")
    try:
        # Fetch all tasks (RLS will filter based on policies, but we also filter in code)
        response = supabase.table("tasks").select("*").execute()
        all_tasks = response.data or []
        filtered = [t for t in all_tasks if t.get("creator_id") == profile_id or t.get("assignee_id") == profile_id]
        return jsonify(filtered)
    except Exception as e:
        print(f"list_tasks error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to fetch tasks", "details": str(e)}), 500

@app.route("/api/tasks", methods=["POST"])
def create_task():
    user = get_user_from_request()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    title = data.get("title")
    assignee_id = data.get("assignee_id")
    description = data.get("description", "")

    if not title or not assignee_id:
        return jsonify({"error": "Title and assignee_id are required"}), 400

    try:
        new_task = {
            "title": title,
            "description": description,
            "status": "Open",
            "creator_id": user.get("id"),
            "assignee_id": assignee_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        result = supabase.table("tasks").insert(new_task).execute()
        if not result.data:
            return jsonify({"error": "Failed to create task"}), 500

        # Send email notification (optional)
        assignee = supabase.table("profiles").select("email").eq("id", assignee_id).execute()
        if assignee.data and assignee.data[0].get("email"):
            send_task_created_email(assignee.data[0]["email"], title)

        return jsonify(result.data[0]), 201
    except Exception as e:
        print(f"create_task error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/tasks/<task_id>", methods=["PATCH"])
def update_task(task_id):
    user = get_user_from_request()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    status = data.get("status")
    if status not in ["Open", "In Progress", "Completed"]:
        return jsonify({"error": "Invalid status"}), 400

    try:
        updated = supabase.table("tasks").update({
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()

        if not updated.data:
            return jsonify({"error": "Task not found"}), 404

        task = updated.data[0]
        if status == "Completed":
            assignee = supabase.table("profiles").select("email").eq("id", task.get("assignee_id")).execute()
            if assignee.data and assignee.data[0].get("email"):
                send_task_completed_email(assignee.data[0]["email"], task.get("title"))

        return jsonify(task)
    except Exception as e:
        print(f"update_task error: {e}")
        return jsonify({"error": str(e)}), 500

# ---------- USERS ----------
@app.route("/api/users", methods=["GET"])
def list_users():
    user = get_user_from_request()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        users = supabase.table("profiles").select("id,email,full_name").execute()
        return jsonify(users.data)
    except Exception as e:
        print(f"list_users error: {e}")
        return jsonify({"error": str(e)}), 500

@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Authorization,Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PATCH,OPTIONS"
    return response

if __name__ == "__main__":
    app.run(debug=True)