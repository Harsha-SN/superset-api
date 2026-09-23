from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

CORS(app)


# ============================================================
# SUPERSET CONFIGURATION
# ============================================================

SUPERSET_URL = os.getenv("SUPERSET_URL")

SUPERSET_USERNAME = os.getenv("SUPERSET_USERNAME")

SUPERSET_PASSWORD = os.getenv("SUPERSET_PASSWORD")

SUPERSET_PROVIDER = os.getenv("SUPERSET_PROVIDER", "db")

SUPERSET_REFRESH = os.getenv("SUPERSET_REFRESH", "True").lower() == "true"

# Your embedded dashboard UUID
SUPERSET_DASHBOARD_UUID = os.getenv(
    "SUPERSET_DASHBOARD_UUID"
)


# ============================================================
# GET SUPERSET ACCESS TOKEN
# ============================================================

def get_superset_access_token():

    login_url = (
        f"{SUPERSET_URL}/api/v1/security/login"
    )

    payload = {
        "username": SUPERSET_USERNAME,
        "password": SUPERSET_PASSWORD,
        "provider": SUPERSET_PROVIDER,
        "refresh": SUPERSET_REFRESH
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(
        login_url,
        json=payload,
        headers=headers,
        timeout=15
    )

    if response.status_code != 200:

        raise Exception(
            "Superset login failed: "
            f"{response.status_code} - "
            f"{response.text}"
        )

    result = response.json()

    access_token = result.get("access_token")

    if not access_token:

        raise Exception(
            "Superset login succeeded, "
            "but no access_token was returned."
        )

    return access_token


# ============================================================
# GET GUEST TOKEN
# ============================================================

def get_guest_token():

    access_token = get_superset_access_token()

    guest_token_url = (
        f"{SUPERSET_URL}/api/v1/security/guest_token/"
    )

    payload = {

        "resources": [
            {
                "type": "dashboard",
                "id": SUPERSET_DASHBOARD_UUID
            }
        ],

        "rls": [],

        "user": {
            "username": "streamlit_guest",
            "first_name": "Streamlit",
            "last_name": "User"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": (
            f"Bearer {access_token}"
        )
    }

    response = requests.post(
        guest_token_url,
        json=payload,
        headers=headers,
        timeout=15
    )

    if response.status_code != 200:

        raise Exception(
            "Guest token request failed: "
            f"{response.status_code} - "
            f"{response.text}"
        )

    result = response.json()

    token = result.get("token")

    if not token:

        raise Exception(
            "Guest token response did not "
            "contain a token."
        )

    return token


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "success",
        "message": "Superset Guest Token API is running"
    })


# ============================================================
# GUEST TOKEN ENDPOINT
# ============================================================

@app.route(
    "/api/superset/guest-token",
    methods=["GET"]
)
def guest_token():

    try:

        token = get_guest_token()

        return jsonify({
            "token": token
        })

    except Exception as e:

        print(
            "[GUEST TOKEN ERROR]",
            str(e)
        )

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("SUPERSET GUEST TOKEN SERVICE")
    print("=" * 70)

    print(
        "Superset URL:"
        f" {SUPERSET_URL}"
    )

    print(
        "Dashboard UUID:"
        f" {SUPERSET_DASHBOARD_UUID}"
    )

    print(
        "Guest Token API:"
        " http://127.0.0.1:5001/"
        "api/superset/guest-token"
    )

    print("=" * 70)

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )
