import datetime as dt
import sqlalchemy as sa
from app.db import Base
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime


class utcnow(expression.FunctionElement):
    type = DateTime()


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


class TimestampableMixin:
    """Allow a model to track its creation and update times"""

    created_at = sa.Column(sa.DateTime, nullable=False, default=utcnow())
    updated_at = sa.Column(
        sa.DateTime,
        nullable=False,
        server_default=utcnow(),
        onupdate=utcnow(),
    )


class User(TimestampableMixin, Base):
    """Model for users"""

    __tablename__ = "user"

    id = sa.Column(
        sa.Integer, sa.Identity(start=1, increment=1), primary_key=True, index=True
    )
    name = sa.Column(sa.String, nullable=False)
    email = sa.Column(
        sa.String, nullable=False, index=True, unique=True, doc="email of user required"
    )
    email_opt_in = sa.Column(sa.Boolean, nullable=False, default=True)
    hashed_password = sa.Column(sa.String, nullable=False)
    birthday = sa.Column(sa.Date, nullable=False)
    scopes = sa.Column(sa.String, default="basic", nullable=False)
    active = sa.Column(sa.Boolean, nullable=False, default=True)
    member = sa.orm.relationship("Member", back_populates="user")
    payment = sa.orm.relationship("Payment", back_populates="user")


class Member(TimestampableMixin, Base):
    __tablename__ = "member"

    id = sa.Column(
        sa.Integer, sa.Identity(start=1, increment=1), primary_key=True, index=True
    )
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), primary_key=True)
    member_type_id = sa.Column(
        sa.Integer, sa.ForeignKey("member_type.id"), primary_key=True
    )
    date_start = sa.Column(sa.Date, nullable=False)
    date_end = sa.Column(sa.Date, nullable=False)
    active = sa.orm.column_property(date_end > sa.func.now())
    user = sa.orm.relationship("User", back_populates="member")
    member_type = sa.orm.relationship("MemberType", back_populates="member")
    # payment_id = sa.Column(sa.Integer, sa.ForeignKey("payment.id"), nullable=False)
    # payment = sa.orm.relationship("Payment")


# class Waitinglist(TimestampableMixin, Base):
#     __tablename__ = "membership_waitinglist"

#     id = sa.Column(sa.Integer, autoincrement=True, primary_key=True, index=True)
#     user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), primary_key=True)
#     membership_type_id = sa.Column(
#         sa.Integer, sa.ForeignKey("membership_types.id"), primary_key=True
#     )
#     active = sa.Column(sa.Boolean, default=False, nullable=False)
#     user = sa.orm.relationship("User", back_populates="membership_waiting")
#     membership_type = sa.orm.relationship(
#         "MembershipType", back_populates="user_waiting"
#     )


class MemberType(TimestampableMixin, Base):
    """Model for member types"""

    __tablename__ = "member_type"

    id = sa.Column(
        sa.Integer, sa.Identity(start=1, increment=1), primary_key=True, index=True
    )
    name = sa.Column(sa.String, nullable=False)
    slots_available = sa.Column(sa.Integer, default=0, nullable=False)
    open_public = sa.Column(sa.Boolean, default=False, nullable=False)
    open_waitinglist = sa.Column(sa.Boolean, default=False, nullable=False)
    active = sa.Column(sa.Boolean, default=True, nullable=False)
    member = sa.orm.relationship("Member", back_populates="member_type")


# class Participant(TimestampableMixin, Base):
#     __tablename__ = "participant"

#     user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), primary_key=True)
#     event_id = sa.Column(sa.Integer, sa.ForeignKey("event.id"), primary_key=True)
#     payment_id = sa.Column(sa.Integer, nullable=True)
#     user = sa.orm.relationship("User", back_populates="participant")
#     event = sa.orm.relationship("Event", back_populates="participant")


# class Event(TimestampableMixin, Base):
#     __tablename__ = "event"

#     id = sa.Column(
#         sa.Integer, sa.Identity(start=1, increment=1), primary_key=True, index=True
#     )
#     name = sa.Column(sa.String, nullable=False)
#     slots_available = sa.Column(sa.Integer, default=0, nullable=False)


class Payment(TimestampableMixin, Base):
    __tablename__ = "payment"

    id = sa.Column(
        sa.Integer, sa.Identity(start=1, increment=1), primary_key=True, index=True
    )
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"))
    amount = sa.Column(sa.Numeric, nullable=False)
    paid = sa.Column(sa.Boolean, default=False, nullable=False)
    user = sa.orm.relationship("User", back_populates="payment")


class Doorevent(Base):
    __tablename__ = "door_event"

    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), primary_key=True)
    created_at = sa.Column(
        sa.DateTime,
        nullable=False,
        default=sa.func.current_timestamp(),
        primary_key=True,
    )
