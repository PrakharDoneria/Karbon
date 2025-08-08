import requests
from token_manager import get_token, NETLIFY_SERVICE

def test_netlify_token():
    token = get_token(NETLIFY_SERVICE)
    if not token:
        print("❌ No Netlify token found. Please save it first using token_manager.py")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = "https://api.netlify.com/api/v1/sites"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        sites = response.json()
        print("✅ Token works! Found the following sites:")
        for site in sites:
            print(f" - {site.get('name')} ({site.get('url')})")
    else:
        print(f"❌ API call failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_netlify_token()
