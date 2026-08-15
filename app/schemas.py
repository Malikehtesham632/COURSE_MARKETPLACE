"""
Pydantic schemas: these define what shape of data the API accepts
(request bodies) and what shape of data it sends back (response bodies).

Kept separate from models.py on purpose - a model describes what the
database table actually stores, a schema describes what the outside
world is allowed to see or send. For example, password_hash exists on
the User model but is never included in any schema that goes out.
"""

from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """Data required to register a new user."""

    name: str
    email: EmailStr
    password: str
    is_instructor: bool = False

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        """Custom validation: reject weak passwords before they reach the database."""
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if value.isdigit():
            raise ValueError("Password cannot be only numbers")
        return value


class UserOut(BaseModel):
    """Public-safe view of a user. password_hash is deliberately not included."""

    id: int
    name: str
    email: EmailStr
    is_instructor: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Data required to log in."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Shape of the response returned after a successful login."""

    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Course schemas
# ---------------------------------------------------------------------------

class OwnerOut(BaseModel):
    """A small nested model - just enough owner info to embed inside a course."""

    id: int
    name: str

    class Config:
        from_attributes = True


class CourseCreate(BaseModel):
    """Data required to create a new course."""

    title: str
    description: Optional[str] = None
    price: float

    @field_validator("price")
    @classmethod
    def price_must_be_reasonable(cls, value: float) -> float:
        """Custom validation: price must be a sensible positive number."""
        if value <= 0:
            raise ValueError("Price must be greater than 0")
        if value > 100000:
            raise ValueError("Price must be less than 100,000")
        return value


class CourseReplace(BaseModel):
    """Full replacement of a course - used by PUT. Every field is required."""

    title: str
    description: Optional[str] = None
    price: float


class CourseUpdate(BaseModel):
    """Partial update of a course - used by PATCH. Every field is optional."""

    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None


class CourseOut(BaseModel):
    """Public view of a course, with the owner's info nested inside it."""

    id: int
    title: str
    description: Optional[str]
    price: float
    owner_id: int
    owner: OwnerOut
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Order schemas
# ---------------------------------------------------------------------------

class OrderCreate(BaseModel):
    """Data required to buy a course."""

    course_id: int


class OrderOut(BaseModel):
    """Public view of an order, with the purchased course nested inside it."""

    id: int
    buyer_id: int
    course: CourseOut
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
