from sqlalchemy.orm import DeclarativeBase


# Modern approach (SQLAlchemy 2.0+)
class Base(DeclarativeBase):
    pass


# Register the models for Migration
from . import (  # noqa: E402, F401
    user,
    landing,
    otp,
    token,
    program,
    registration,
    payment,
    contact,
    membership,
    membership_registration,
    course,
    app_settings,
)
