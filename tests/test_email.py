# ** Base Modules
import pytest
from pydantic import ValidationError

# ** App Modules
from app.schema.auth import AdminUserCreate
from app.schema.contact import ContactCreate
from app.schema.email import validate_email_address

# Addresses that must be accepted.
VALID = [
    "name@example.com",
    "first.last@sub.example.co.uk",
    "a+tag@example.io",
    "x1@e-x.com",
]

# The ones `<input type="email">` waves through and a schema must not: an @ and
# something either side of it is not an address anyone can be reached at.
INVALID = [
    "abc@abc",
    "a@b",
    "name@localhost",
    "plainaddress",
    "name@@example.com",
    "name@.com",
    "name@example.",
    ".name@example.com",
    "na me@example.com",
    "name@example..com",
]


@pytest.mark.parametrize("address", VALID)
def test_valid_addresses_are_accepted(address: str) -> None:
    assert validate_email_address(address) == address


@pytest.mark.parametrize("address", INVALID)
def test_invalid_addresses_are_rejected(address: str) -> None:
    with pytest.raises(ValueError):
        validate_email_address(address)


def test_surrounding_space_is_trimmed() -> None:
    assert validate_email_address("  name@example.com  ") == "name@example.com"


def test_blank_is_absent_rather_than_empty() -> None:
    # "" on a unique column collides with every other blank one.
    assert validate_email_address("") is None
    assert validate_email_address("   ") is None
    assert validate_email_address(None) is None


def test_required_rejects_blank() -> None:
    with pytest.raises(ValueError):
        validate_email_address("", required=True)


def test_the_function_and_the_schemas_agree() -> None:
    """
    The Form()-based profile route uses the function and everything else uses
    EmailStr; a disagreement between them would mean an address the site accepts
    in one place and rejects in another.
    """
    fields = dict(full_name="A Person", phone="+60123456789", subject="Hi", message="Hello")

    for address in VALID:
        assert ContactCreate(email=address, **fields).email == address

    for address in INVALID:
        with pytest.raises(ValidationError):
            ContactCreate(email=address, **fields)


def test_an_account_needs_a_way_to_be_reached() -> None:
    # Mirrors the guard on the profile route: both columns are nullable, but an
    # account with neither can never sign in.
    with pytest.raises(ValidationError):
        AdminUserCreate(full_name="A Person")

    assert AdminUserCreate(full_name="A Person", email="name@example.com").email == "name@example.com"
    assert AdminUserCreate(full_name="A Person", phone_number="+60123456789").email is None
