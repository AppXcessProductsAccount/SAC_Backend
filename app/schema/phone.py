"""
The one place a phone number is judged, for every form that collects one.

The public site and the admin both submit E.164 ("+60123456789") from their
PhoneField component, which validates in the browser against libphonenumber's
per-country rules. This is that same check on the server, so a request that
skips the UI — a direct API call, a stale tab, a script — cannot store a number
the UI would have refused.

"Valid" here means valid *for the country the number itself declares*: a
Singapore mobile is 8 national digits, a Malaysian one 9-10, an Indian one 10.
One shared length rule would either reject real Malaysian numbers or wave
through half-typed Singaporean ones, so this defers to libphonenumber's own
per-country table rather than to a regex.

Numbers are normalised to E.164 before they are stored, so the same person's
number is a single string however it was typed, and `User.phone_number`'s
uniqueness constraint compares like with like.

Use `PhoneNumber` where a number is mandatory and `OptionalPhoneNumber` where it
is not; `validate_phone` is the same check for the one route that takes its
fields as `Form()` values instead of through a schema.
"""

from typing import Annotated, Optional

import phonenumbers
from phonenumbers import NumberParseException
from pydantic import BeforeValidator

# The country a number with no "+" prefix is read as. Matches the PhoneField's
# `defaultCountry`, so the two ends agree on what a bare local number means.
DEFAULT_REGION = "SG"

_NO_COUNTRY = (
    "Enter a valid phone number including its country code, for example "
    "+60123456789."
)


def validate_phone(value: object, *, required: bool = False) -> Optional[str]:
    """
    Return `value` as an E.164 string, or raise `ValueError` explaining why not.

    Blank input is `None` rather than "", so an optional number that was left
    empty is stored as absent instead of as an empty string that later reads as
    a real value.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ValueError("A phone number is required.")
        return None

    if not isinstance(value, str):
        raise ValueError(_NO_COUNTRY)

    raw = value.strip()

    # Only a "+" prefix says which country the digits belong to. Without one the
    # number is read as DEFAULT_REGION, which keeps older clients that post a
    # bare local number working — the browser field always sends the prefix.
    region = None if raw.startswith("+") else DEFAULT_REGION

    try:
        parsed = phonenumbers.parse(raw, region)
    except NumberParseException:
        raise ValueError(_NO_COUNTRY) from None

    if not phonenumbers.is_valid_number(parsed):
        # Naming the country is the whole point of the message: by far the
        # commonest failure is a real number sent under the wrong country code,
        # and "invalid phone number" gives no clue which half is wrong.
        if region is not None:
            # There was no "+", so the digits were judged as DEFAULT_REGION. The
            # country libphonenumber ends up reporting here is not trustworthy �
            # a leading "0" can be re-read as a dial-out prefix, which lands the
            # number on some unrelated country entirely. Name the region it was
            # actually measured against and ask for the prefix instead.
            raise ValueError(
                f"That is not a valid {region} phone number. Include the country "
                "code, for example +60123456789."
            )
        country = phonenumbers.region_code_for_number(parsed)
        named = f"{country} (+{parsed.country_code})" if country else f"+{parsed.country_code}"
        raise ValueError(
            f"That is not a valid phone number for {named}. "
            "Check the digits, or select the country the number belongs to."
        )

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def _required(value: object) -> str:
    return validate_phone(value, required=True)  # type: ignore[return-value]


def _optional(value: object) -> Optional[str]:
    return validate_phone(value, required=False)


#: A number that must be present and valid.
PhoneNumber = Annotated[str, BeforeValidator(_required)]

#: A number that may be omitted, but must be valid when given.
OptionalPhoneNumber = Annotated[Optional[str], BeforeValidator(_optional)]
