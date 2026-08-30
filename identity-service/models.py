import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum
from database import Base


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    INVESTIGATING_OFFICER = "INVESTIGATING_OFFICER"
    COURT_CLERK = "COURT_CLERK"
    JUDGE = "JUDGE"
    NCRB_ANALYST = "NCRB_ANALYST"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    organization = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)

    mfa_secret = Column(String, nullable=True)      # set once MFA setup is initiated
    mfa_enabled = Column(Boolean, nullable=False, default=False)  # only True after the user verifies a code
