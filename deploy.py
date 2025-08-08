from deploy_vercel import deploy_vercel
from deploy_netlify import deploy_netlify


if __name__ == "__main__":
    choice = input("Deploy to (vercel/netlify): ").strip().lower()
    if choice == "vercel":
        deploy_vercel()
    elif choice == "netlify":
        deploy_netlify()
    else:
        print("❌ Unknown choice. Use 'vercel' or 'netlify'.")
