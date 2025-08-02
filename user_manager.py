import os
import json

USER_DIR = "user_data"
ACTIVE_USER_FILE = os.path.join(USER_DIR, "active_user.json")

class UserManager:
    def __init__(self, users_dir="user_data"):
        self.users_dir = users_dir
        os.makedirs(self.users_dir, exist_ok=True)
        
        self.active_user_file = os.path.join(self.users_dir, "active_user.json")
    def set_active_user(self, username):
        with open(self.active_user_file, 'w') as f:
            json.dump({"active_user": username}, f, indent=4)
    def get_active_user(self):
        if os.path.exists(self.active_user_file):
            with open(self.active_user_file, 'r') as f:
                data = json.load(f)
                return data.get("active_user", None)
        return None
           

    def list_users(self):
        return [
            f.replace(".json", "")
            for f in os.listdir(USER_DIR)
            if f.endswith(".json") and f != "active_user.json"
        ]

    def create_user(self, username):
        filepath = os.path.join(USER_DIR, f"{username}.json")
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                json.dump({"prompt_history": [], "settings": {}}, f)
            return True
        return False  # User already exists

    def switch_user(self, username):
        filepath = os.path.join(USER_DIR, f"{username}.json")
        if os.path.exists(filepath):
            with open(ACTIVE_USER_FILE, "w") as f:
                json.dump({"active_user": username}, f)
            return True
        return False  # User does not exist

    def get_active_user(self):
        with open(ACTIVE_USER_FILE, "r") as f:
            return json.load(f)["active_user"]

    def get_user_data(self, username):
        filepath = os.path.join(USER_DIR, f"{username}.json")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
        return None

    def save_user_data(self, username, data):
        filepath = os.path.join(USER_DIR, f"{username}.json")
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
