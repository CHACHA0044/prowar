"""
SQLAlchemy Declarative Base.
All ORM models inherit from Base.
"""

from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func


class Base(DeclarativeBase):
    """Base model providing shared attributes."""
    pass

