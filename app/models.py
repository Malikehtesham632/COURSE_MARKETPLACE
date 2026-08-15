"""
SQLAlchemy models: these describe the real tables in the database,
their columns, and how the tables relate to each other.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    """A registered user - either an instructor, a student, or both."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    # Only the bcrypt hash is ever stored - never the real password.
    password_hash = Column(String, nullable=False)
    is_instructor = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # One user can own many courses, and place many orders.
    courses = relationship("Course", back_populates="owner")
    orders = relationship("Order", back_populates="buyer")


class Course(Base):
    """A course listed for sale by an instructor."""

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    # Foreign key: links this course to the user who created it.
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="courses")
    orders = relationship("Order", back_populates="course")


class Order(Base):
    """A record of one user buying one course."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    # Foreign keys: link this order to the buyer and to the purchased course.
    buyer_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)

    buyer = relationship("User", back_populates="orders")
    course = relationship("Course", back_populates="orders")
