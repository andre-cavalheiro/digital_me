from fury_api.lib.security import create_long_lived_token

if __name__ == "__main__":
    # Generate a token for admin use (to be set in the environment variable FURY_API_ADMIN_TOKEN)
    admin_token = create_long_lived_token(
        token_id="admin",  # or any identifier you want
        name="Admin",      # admin name
        email="admin@example.com"  # admin email
    )
    print(f"Bearer {admin_token}")
