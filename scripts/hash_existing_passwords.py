import sys
import os
# NOTE: Hardcoded Supabase credentials as per user request for self-contained execution.
# This should be reverted to environment variables (os.environ.get) in a production setting.
SUPABASE_URL = "https://jiwjcittpzjsgnmecuaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imppd2pjaXR0cHpqc2dubWVjdWF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM5ODYxMjksImV4cCI6MjA3OTU2MjEyOX0.d7MLjBBzFHNmGyS3VRqoo1EjoZ6xtzabUenOGYR2YoE"

from supabase import create_client, Client

# Add the project root to sys.path to allow importing utils.auth
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Check if utils.auth is available in the environment path
try:
    from utils.auth import hash_password
except ImportError:
    print("Error: utils/auth.py or its hash_password function is not found.")
    print("Ensure the file exists and is accessible for the import.")
    sys.exit(1)

try:
    # Initialize the Supabase client using hardcoded keys
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    sys.exit(1)


def main():
    print("--- Starting Automated Password Hashing Migration ---")
    
    # NOTE: The migration relies on RLS being disabled or the service role key being used.
    
    table_name = "users"
    
    print(f"Fetching users from '{table_name}' table...")
    try:
        res = supabase.table(table_name).select("username, password").execute()
    except Exception as e:
        print(f"Error fetching data from Supabase: {e}")
        return

    if not res.data:
        print(f"No users found in the '{table_name}' table. Exiting.")
        return

    users_updated = 0
    for user in res.data:
        password = user.get("password")
        username = user.get("username")
        
        # Check if the password is NOT a valid bcrypt hash (starts with $2b$)
        if password and not password.startswith("$2b$"):
            
            print(f"Hashing password for user: {username}")
            try:
                # The assumption is that hash_password uses bcrypt or a compatible library
                hashed_pw = hash_password(password)
                
                # Perform the update
                update_res = supabase.table(table_name).update({"password": hashed_pw}).eq("username", username).execute()
                
                # Check for errors and data in the update response
                if update_res.data:
                    print(f"Successfully updated password for {username}")
                    users_updated += 1
                elif hasattr(update_res, 'error') and update_res.error:
                    print(f"ERROR updating {username}: {update_res.error}")
                else:
                    print(f"WARNING: No records updated for {username}. It might be that the user does not exist or no change was needed.")
            except Exception as e:
                print(f"CRITICAL ERROR hashing password for {username}: {e}")
        elif not password:
            print(f"Skipping user: {username} (Empty/Null password)")
        else:
            print(f"Password for user {username} is already hashed. Skipping.")

    print(f"--- Password Hashing Complete. {users_updated} users updated. ---")

if __name__ == "__main__":
    main()