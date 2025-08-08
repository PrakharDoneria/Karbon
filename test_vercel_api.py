import requests
from token_manager import get_token

VERCEL_SERVICE = "vercel"

def test_vercel_token():
    token = get_token(VERCEL_SERVICE)
    if not token:
        print("❌ No Vercel token found. Please save it first using token_manager.py")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = "https://api.vercel.com/v9/projects"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        projects = response.json().get("projects", [])
        print("✅ Token works! Found the following projects:")
        for proj in projects:
            print(f" - {proj.get('name')} (ID: {proj.get('id')})")
    else:
        print(f"❌ API call failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_vercel_token()
