# Production Preparation Checklist

The following tasks have been identified as necessary steps to prepare the **Galaxy CRM** for a production environment. Execute these when the "Prepare for Production" command is given.

## Security Hardening
- [ ] **Remove Developer Backdoor**: Remove the `DEV_USERNAME` / `DEV_PASSWORD` bypass checks in `check_login` and the "User Management (Dev Only)" panel in `app.py`.
- [ ] **Migrate to Secure Hashing**: 
    - Switch from Reversible Encryption (Fernet) to One-Way Hashing (e.g., `bcrypt`).
    - Create a migration script to hash all existing encrypted passwords.
    - Update `check_login` to verify hashes.
- [ ] **Disable Plaintext Exposure**: Ensure no UI components (like the Admin Panel) display user passwords.

## Bug Fixes & Logic
- [ ] **Fix Staff Assignment Logic**: Uncomment and fix the `staff_assignment_map` logic in the Staff Management tab (`app.py`) to correctly show "📍 Assigned Project" indicators.
