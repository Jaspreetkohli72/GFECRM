from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashes a password using pbkdf2_sha256."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def update_password_with_recovery_key(supabase_client, username, recovery_key, new_password):
    """
    Custom recovery: Verifies username and recovery_key, then updates password.
    Returns True on success, False otherwise.
    """

    # 1. Verify existence of user and recovery_key
    res = supabase_client.table("users").select("username").eq("username", username).eq("recovery_key", recovery_key).execute()

    if not (res and res.data):
        return False

    # 2. Hash new password and update
    new_hashed_password = hash_password(new_password)

    # NOTE: We are using the Supabase client passed from app.py
    update_res = supabase_client.table("users").update({"password": new_hashed_password}).eq("username", username).execute()

    # 3. Check for successful update (supabase-py v2 returns data on success)
    return bool(update_res.data)
