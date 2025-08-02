from user_manager import UserManager

manager = UserManager()

# List existing users
print("Users:", manager.list_users())

# Set active user to 'jyothi'
manager.set_active_user("jyothi")

# Check who is the active user now
print("Active User:", manager.get_active_user())
