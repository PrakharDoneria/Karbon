import requests
import json
from token_manager import get_token, NETLIFY_SERVICE

def deploy_netlify():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        site_id = config["netlify_site_id"]
    except (FileNotFoundError, KeyError):
        print("❌ Missing Netlify site ID in config.json")
        return

    token = get_token(NETLIFY_SERVICE)
    if not token:
        print("❌ No Netlify token found. Save it first with token_manager.py")
        return

    url = f"https://api.netlify.com/api/v1/sites/{site_id}/builds"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(url, headers=headers)
    if response.status_code == 201:
        print("✅ Netlify deployment triggered!")
    else:
        print(f"❌ Netlify deployment failed: {response.status_code} - {response.text}")
