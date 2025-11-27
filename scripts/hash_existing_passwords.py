import os
from supabase import create_client, Client
from utils.auth import hash_password

# Load environment variables
# Ensure SUPABASE_URL and SUPABASE_KEY are set in your environment
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def main():
    print("--- Starting Password Hashing Migration ---")

    # NOTE: RLS must be disabled or the service role key must be used for this script to work.
    # The image shows RLS is disabled, which is good for this migration.

    # Fetch all users
    res = supabase.table("users").select("id, username, password").execute()

    if not res.data:
        print("No users found in the 'users' table.")
        return

    users_updated = 0
    for user in res.data:
        # Check if the password is NOT a valid bcrypt hash (starts with $2b$)
        if not user.get("password", "").startswith("$2b$"):
            
            # Skip records with null or empty passwords, though 'text' column should prevent nulls.
            if not user.get("password"):
                print(f"Skipping user: {user['username']} (Empty password)")
                continue

            print(f"Hashing password for user: {user['username']}")
            try:
                hashed_pw = hash_password(user["password"])
                # Perform the update
                update_res = supabase.table("users").update({"password": hashed_pw}).eq("id", user["id"]).execute()
                
                if update_res.error:
                    print(f"ERROR updating {user['username']}: {update_res.error}")
                else:
                    users_updated += 1
            except Exception as e:
                print(f"CRITICAL ERROR hashing password for {user['username']}: {e}")

    print(f"--- Password Hashing Complete. {users_updated} users updated. ---")

if __name__ == "__main__":
    main()
