import datetime as dt
import sqlalchemy as sa
from app.db import Base


class TimestampableMixin:
    """Allow a model to track its creation and update times"""

    created_at = sa.Column(
        sa.DateTime, nullable=False, default=sa.func.current_timestamp()
    )
    updated_at = sa.Column(
        sa.DateTime,
        nullable=False,
        default=sa.func.current_timestamp(),
        onupdate=sa.func.current_timestamp(),
    )


class User(TimestampableMixin, Base):
    """Model for users"""

    __tablename__ = "users"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True, index=True)
    name = sa.Column(sa.String, nullable=False)
    email = sa.Column(
        sa.String, nullable=False, index=True, unique=True, doc="email of user required"
    )
    hashed_password = sa.Column(sa.String, nullable=False)
    birthday = sa.Column(sa.Date, nullable=False)
    is_admin = sa.Column(sa.Boolean, default=False, nullable=False)
    active = sa.Column(sa.Boolean, nullable=False, default=True)


class Membership(TimestampableMixin, Base):
    __tablename__ = "membership"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True, index=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), primary_key=True)
    membership_type_id = sa.Column(
        sa.Integer, sa.ForeignKey("membership_types.id"), primary_key=True
    )
    date_start = sa.Column(sa.Date, nullable=False)
    date_end = sa.Column(sa.Date, nullable=False)
    active = sa.orm.column_property(date_end > sa.func.now())
    user = sa.orm.relationship("User", back_populates="membership_member")
    membership_type = sa.orm.relationship(
        "MembershipType", back_populates="user_member"
    )
    payment_id = sa.Column(sa.Integer, sa.ForeignKey("payments.id"), nullable=False)
    payment = sa.orm.relationship("Payment")


class Waitinglist(TimestampableMixin, Base):
    __tablename__ = "membership_waitinglist"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True, index=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), primary_key=True)
    membership_type_id = sa.Column(
        sa.Integer, sa.ForeignKey("membership_types.id"), primary_key=True
    )
    active = sa.Column(sa.Boolean, default=False, nullable=False)
    user = sa.orm.relationship("User", back_populates="membership_waiting")
    membership_type = sa.orm.relationship(
        "MembershipType", back_populates="user_waiting"
    )


class MembershipType(TimestampableMixin, Base):
    """Model for membership types"""

    __tablename__ = "membership_types"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True, index=True)
    name = sa.Column(sa.String, nullable=False)
    slots = sa.Column(sa.Integer, default=0, nullable=False)
    slots_available = sa.Column(sa.Integer, default=0, nullable=False)


class Event(TimestampableMixin, Base):
    __tablename__ = "events"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True, index=True)
    name = sa.Column(sa.String, nullable=False)
    slots = sa.Column(sa.Integer, default=0, nullable=False)


class Payment(TimestampableMixin, Base):
    __tablename__ = "payments"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True, index=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), primary_key=True)
    amount = sa.Column(sa.Numeric, nullable=False)
    paid = sa.Column(sa.Boolean, default=False, nullable=False)
    user = sa.orm.relationship("User", back_populates="payments")


class Doorevent(Base):
    __tablename__ = "door_event"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True, index=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), primary_key=True)
    created_at = sa.Column(
        sa.DateTime, nullable=False, default=sa.func.current_timestamp()
    )


# class AuditLog(TimestampableMixin, Base):
#     """Model an audit log of user actions"""
#     __tablename__ = "auditlog"

#     user_id = db.Column(db.Integer, doc="The ID of the user who made the change")
#     target_type = db.Column(db.String(100), nullable=False, doc="The table name of the altered object")
#     target_id = db.Column(db.Integer, doc="The ID of the altered object")
#     action = db.Column(db.Integer, doc="Create (1), update (2), or delete (3)")
#     state_before = db.Column(db.Text, doc="Stores a JSON string representation of a dict containing the altered column "
#                                           "names and original values")
#     state_after = db.Column(db.Text, doc="Stores a JSON string representation of a dict containing the altered column "
#                                          "names and new values")
