"""SQLAlchemy async declarative base."""

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(DeclarativeBase):
    """Base class for all ORM models.

    Using the modern DeclarativeBase approach (SQLAlchemy 2.0+).
    """

    pass
