# ** Base Modules
import pytest
from pydantic import ValidationError

# ** App Modules
from app.schema.contact import ContactCreate
from app.schema.phone import PhoneNumber, OptionalPhoneNumber, validate_phone
from app.schema.program import RegistrationCreate

from pydantic import BaseModel


class _Model(BaseModel):
    required: PhoneNumber
    optional: OptionalPhoneNumber = None


# Each number is judged by ITS OWN country's rules, which is the whole point:
# a single shared length check would reject real Malaysian numbers or accept
# half-typed Singaporean ones.
VALID = [
    ("+60123456789", "Malaysia, 9 national digits"),
    ("+601123456789", "Malaysia, 10 national digits"),
    ("+6591234567", "Singapore, 8 digits"),
    ("+919876543210", "India, 10 digits"),
    ("+14155552671", "United States, 10 digits"),
    ("+442071838750", "United Kingdom"),
]

INVALID = [
    ("+6012345678901", "Malaysia, 11 digits is past the maximum"),
    ("+6012345", "Malaysia, too short"),
    ("+65912345", "Singapore, too short"),
    ("+91987654321", "India, 9 digits"),
    ("+1415555267", "United States, 9 digits"),
    ("not a number", "no digits at all"),
    ("12345", "no country code and too short for the default region"),
]


@pytest.mark.parametrize("number,label", VALID, ids=[label for _, label in VALID])
def test_valid_numbers_are_accepted(number: str, label: str) -> None:
    assert validate_phone(number) == number


@pytest.mark.parametrize("number,label", INVALID, ids=[label for _, label in INVALID])
def test_invalid_numbers_are_rejected(number: str, label: str) -> None:
    with pytest.raises(ValueError):
        validate_phone(number)


def test_number_is_normalised_to_e164() -> None:
    # However it is typed, one person's number is stored as one string — which is
    # what makes User.phone_number's uniqueness constraint meaningful.
    assert validate_phone("+60 12-345 6789") == "+60123456789"
    assert validate_phone("+60 (12) 345 6789") == "+60123456789"


def test_blank_is_absent_rather_than_empty() -> None:
    assert validate_phone("") is None
    assert validate_phone("   ") is None
    assert validate_phone(None) is None


def test_required_rejects_blank() -> None:
    with pytest.raises(ValueError):
        validate_phone("", required=True)


def test_error_names_the_country_for_a_prefixed_number() -> None:
    with pytest.raises(ValueError, match="MY"):
        validate_phone("+6012345678901")


def test_error_asks_for_a_country_code_when_there_is_none() -> None:
    # A bare local number is measured against the default region, and the message
    # must say so rather than naming whatever country libphonenumber lands on
    # after re-reading a leading zero as a dial-out prefix.
    with pytest.raises(ValueError, match="country code"):
        validate_phone("0123456789")


def test_annotated_types_in_a_model() -> None:
    model = _Model(required="+60 12-345 6789")
    assert model.required == "+60123456789"
    assert model.optional is None

    with pytest.raises(ValidationError):
        _Model(required=None)

    with pytest.raises(ValidationError):
        _Model(required="+60123456789", optional="+6012345678901")


def test_enquiry_form_validates_its_phone() -> None:
    fields = dict(full_name="A Person", email="a@example.com", subject="Hello", message="Hi")

    assert ContactCreate(phone="+60123456789", **fields).phone == "+60123456789"

    with pytest.raises(ValidationError):
        ContactCreate(phone="+6012345678901", **fields)

    # The phone is optional on an enquiry, and an omitted one must stay optional.
    assert ContactCreate(**fields).phone is None


def test_registration_validates_its_phones() -> None:
    fields = dict(
        nric_last_4="1234",
        preferred_language="English",
        meal_preference="Vegetarian",
        emergency_contact_name="A Relative",
        emergency_contact_relation="Sister",
        discovery_source="Website",
    )

    ok = RegistrationCreate(emergency_contact_phone="+60 12-345 6789", **fields)
    assert ok.emergency_contact_phone == "+60123456789"
    assert ok.introducer_phone is None

    # Mandatory on a registration: there is no point in an emergency contact we
    # cannot actually call.
    with pytest.raises(ValidationError):
        RegistrationCreate(emergency_contact_phone="", **fields)

    with pytest.raises(ValidationError):
        RegistrationCreate(
            emergency_contact_phone="+6591234567",
            introducer_phone="+6012345678901",
            **fields,
        )
