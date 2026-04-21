import pytest
from rne_cli.errors import RNEValidationError
from rne_cli.siren import validate_siren, luhn_valid


class TestValidateSiren:
    def test_valid_nine_digits(self):
        assert validate_siren("732829320") == "732829320"

    def test_strips_whitespace(self):
        assert validate_siren("  732829320  ") == "732829320"

    def test_rejects_eight_digits(self):
        with pytest.raises(RNEValidationError, match="9 chiffres"):
            validate_siren("12345678")

    def test_rejects_ten_digits(self):
        with pytest.raises(RNEValidationError, match="9 chiffres"):
            validate_siren("1234567890")

    def test_rejects_non_numeric(self):
        with pytest.raises(RNEValidationError, match="9 chiffres"):
            validate_siren("12345678A")

    def test_rejects_empty(self):
        with pytest.raises(RNEValidationError):
            validate_siren("")


class TestLuhn:
    def test_valid_luhn(self):
        # 732829320 is a real, Luhn-valid SIREN (L'Oréal)
        assert luhn_valid("732829320") is True

    def test_invalid_luhn(self):
        assert luhn_valid("123456789") is False


def test_check_siren_returns_luhn_status():
    from rne_cli.siren import check_siren
    norm, ok = check_siren("732829320")  # L'Oréal, valid Luhn
    assert norm == "732829320"
    assert ok is True

    norm, ok = check_siren("123456789")  # invalid Luhn
    assert norm == "123456789"
    assert ok is False
