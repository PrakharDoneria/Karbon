import requests
import json
from token_manager import get_token, VERCEL_SERVICE

def deploy_vercel():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        project_id = config["vercel_project_id"]
    except (FileNotFoundError, KeyError):
        print("❌ Missing Vercel project ID in config.json")
        return

    token = get_token(VERCEL_SERVICE)
    if not token:
        print("❌ No Vercel token found. Save it first with token_manager.py")
        return

    url = "https://api.vercel.com/v13/deployments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": project_id,
        "target": "production"
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in (200, 201):
        print("✅ Vercel deployment triggered!")
    else:
        print(f"❌ Vercel deployment failed: {response.status_code} - {response.text}")
