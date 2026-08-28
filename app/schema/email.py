"""
The one place an email address is judged outside a schema.

Every schema in this app already types its address as pydantic's `EmailStr`,
which is backed by `email_validator` and requires a real, dotted domain — so
`abc@abc`, `a@b` and `name@localhost` are all refused there. What that does not
cover is a route which takes its fields as `Form()` values instead of through a
schema, because nothing validates those on the way in.

This exposes exactly the same check as a plain function, via a `TypeAdapter` over
`EmailStr` rather than a second rule of its own — a regex here would inevitably
drift from what the schemas accept, and an address that one half of the app
accepts and the other rejects is worse than either rule alone.

`validate_email_address` mirrors `app.schema.phone.validate_phone`: blank is
absent rather than empty, and a bad value raises `ValueError` carrying a message
worth showing someone.
"""

from typing import Optional

from pydantic import EmailStr, TypeAdapter, ValidationError

_EMAIL = TypeAdapter(EmailStr)


def validate_email_address(value: object, *, required: bool = False) -> Optional[str]:
    """
    Return `value` as a normalised address, or raise `ValueError` explaining why
    it is not one.

    Blank input is `None` rather than "", so an optional address left empty is
    stored as absent instead of as an empty string that later reads as a real
    value — and, on a unique column, collides with every other blank one.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ValueError("An email address is required.")
        return None

    if not isinstance(value, str):
        raise ValueError("Enter a valid email address, for example name@example.com.")

    try:
        return _EMAIL.validate_python(value.strip())
    except ValidationError:
        # email_validator's own wording leaks its internals ("The part after the
        # @-sign is not valid. It should have a period."). This is the same
        # judgement in words worth putting in front of someone.
        raise ValueError(
            "Enter a valid email address, for example name@example.com."
        ) from None
