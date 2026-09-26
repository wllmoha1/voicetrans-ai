import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.auth import hash_password, verify_password, create_access_token, get_current_user_from_token
from backend.database import SessionLocal, Base, engine
from backend.models import User

def test_auth_flow():
    print("Testing Password Hashing, Verification & JWT...")

    password = "SuperSecretPassword123!"
    hashed = hash_password(password)
    
    assert hashed != password, "Hash must not equal plaintext"
    assert verify_password(password, hashed), "Password verification failed"
    assert not verify_password("WrongPassword", hashed), "Invalid password should fail"
    print("-> Password hashing and verification: PASSED")

    # JWT Token test
    token = create_access_token({"sub": "testuser"})
    assert token and isinstance(token, str), "Token must be a valid string"
    print("-> JWT token creation: PASSED")

    # Database User creation test
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Clean up old test user if exists
        db.query(User).filter(User.username == "testuser_dev").delete()
        db.commit()

        test_user = User(
            username="testuser_dev",
            email="dev@example.com",
            hashed_password=hashed,
            full_name="Test Developer",
            native_language="so",
            target_language="en",
            preferred_voice="male"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        assert test_user.id is not None, "User should have an ID"
        print("-> User database insertion & query: PASSED")

        # Verify lookup via token
        token_for_user = create_access_token({"sub": "testuser_dev"})
        found_user = get_current_user_from_token(token_for_user, db)
        assert found_user is not None and found_user.username == "testuser_dev", "User lookup via JWT failed"
        print("-> JWT User retrieval: PASSED")

        # Clean up
        db.delete(test_user)
        db.commit()
    finally:
        db.close()

    print("\n ALL AUTH & DATABASE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_auth_flow()
