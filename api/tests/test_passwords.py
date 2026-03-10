"""Tests for password hashing and validation."""

from auth.passwords import hash_password, verify_password, validate_password


class TestHashPassword:
    def test_hash_and_verify(self):
        pw = "TestPassword1!"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("Correct1!")
        assert verify_password("Wrong1!", hashed) is False

    def test_hash_format(self):
        hashed = hash_password("Test1234")
        assert hashed.startswith("pbkdf2:")
        parts = hashed.split("$")
        assert len(parts) == 3  # iterations$salt$hash

    def test_unique_salts(self):
        h1 = hash_password("Same1234")
        h2 = hash_password("Same1234")
        assert h1 != h2  # Different salts produce different hashes

    def test_verify_corrupted_hash(self):
        assert verify_password("Test1234", "garbage") is False
        assert verify_password("Test1234", "") is False


class TestValidatePassword:
    def test_valid_password(self):
        assert validate_password("StrongPass1") is None

    def test_too_short(self):
        err = validate_password("Ab1")
        assert "8 characters" in err

    def test_no_uppercase(self):
        err = validate_password("lowercase1")
        assert "uppercase" in err

    def test_no_lowercase(self):
        err = validate_password("UPPERCASE1")
        assert "lowercase" in err

    def test_no_digit(self):
        err = validate_password("NoDigitHere")
        assert "digit" in err
