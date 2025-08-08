import json
import os

CONFIG_FILE = ".tokens.json"
VERCEL_SERVICE = "vercel"
NETLIFY_SERVICE = "netlify"

def save_token(service, token):
    tokens = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            tokens = json.load(f)
    tokens[service] = token
    with open(CONFIG_FILE, "w") as f:
        json.dump(tokens, f)
    print(f"✅ Token saved for {service}.")

def get_token(service):
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            tokens = json.load(f)
            return tokens.get(service)
    return None

if __name__ == "__main__":
    service = input("Enter service name (netlify/vercel): ").strip().lower()
    token = input(f"Enter your {service} token: ").strip()
    save_token(service, token)
