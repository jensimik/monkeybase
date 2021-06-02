import datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as sa_pg

from .db import Base
from .models_utils import (
    DoorAccessEnum,
    SlotTypeEnum,
    TimestampableMixin,
    gen_uuid,
    utcnow,
)


class User(TimestampableMixin, Base):
    """Model for users"""

    __tablename__ = "user"

    id = sa.Column(sa.Integer, sa.Identity(start=1, increment=1), primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    email = sa.Column(sa.String, nullable=False, index=True, unique=True)
    email_opt_in = sa.Column(sa.Boolean, nullable=False, default=True)
    hashed_password = sa.Column(sa.String, nullable=False)
    birthday = sa.Column(sa.Date, nullable=False)
    scopes = sa.Column(sa.String, default="basic", nullable=False)
    active = sa.Column(sa.Boolean, nullable=False, default=True)
    enabled_2fa = sa.Column(sa.Boolean, nullable=False, default=False)
    member = sa.orm.relationship("Member", back_populates="user", lazy="noload")
    payment = sa.orm.relationship("Payment", back_populates="user", lazy="noload")
    webauthn = sa.orm.relationship("Webauthn", back_populates="user", lazy="noload")


class Webauthn(TimestampableMixin, Base):
    """Model for webauthn credidentials"""

    __tablename__ = "webauthn"

    id = sa.Column(sa.Integer, sa.Identity(start=1, increment=1), primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)
    credential = sa.Column(sa.String, nullable=False)
    credential_id = sa.Column(sa.String, nullable=False, index=True, unique=True)
    name = sa.Column(sa.String, nullable=False)
    active = sa.Column(sa.Boolean, default=True)
    user = sa.orm.relationship("User", back_populates="webauthn", lazy="noload")


class Member(TimestampableMixin, Base):
    __tablename__ = "member"

    id = sa.Column(sa.Integer, sa.Identity(start=1, increment=1), primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), primary_key=True)
    member_type_id = sa.Column(
        sa.Integer, sa.ForeignKey("member_type.id"), primary_key=True
    )
    date_start = sa.Column(sa.Date, nullable=False)
    date_end = sa.Column(sa.Date, nullable=False)
    active = sa.orm.column_property(date_end > sa.func.now())
    user = sa.orm.relationship("User", back_populates="member", lazy="noload")
    member_type = sa.orm.relationship(
        "MemberType", back_populates="member", lazy="noload"
    )
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

    id = sa.Column(sa.Integer, sa.Identity(start=1, increment=1), primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    active = sa.Column(sa.Boolean, default=True, nullable=False)
    slot_limit = sa.Column(sa.Integer, default=0, nullable=False)
    slot_enabled = sa.Column(sa.Boolean, default=True, nullable=False)
    door_access = sa.Column(
        sa_pg.ENUM(DoorAccessEnum), nullable=False, default=DoorAccessEnum.NOACCESS
    )
    price = sa.Column(sa.Integer, default=0, nullable=False)  # price in cents
    member = sa.orm.relationship("Member", back_populates="member_type", lazy="noload")


class MemberTypeSlot(TimestampableMixin, Base):
    """model for available slots for a membertype"""

    __tablename__ = "member_type_slot"

    id = sa.Column(sa.Integer, sa.Identity(start=1, increment=1), primary_key=True)
    active = sa.Column(sa.Boolean, default=True, nullable=False)
    key = sa.Column(sa_pg.UUID, nullable=False, default=gen_uuid())
    slot_type = sa.Column(
        sa_pg.ENUM(SlotTypeEnum), nullable=False, default=SlotTypeEnum.OPEN
    )
    reserved_until = sa.Column(sa.DateTime, nullable=False, default=utcnow())
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), nullable=True)
    member_type_id = sa.Column(sa.Integer, sa.ForeignKey("member_type.id"))


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

    id = sa.Column(sa.Integer, sa.Identity(start=1, increment=1), primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)
    amount = sa.Column(sa.Integer, nullable=False)  # in cents
    reserved = sa.Column(sa.Boolean, default=False, nullable=False)
    captured = sa.Column(sa.Boolean, default=False, nullable=False)
    stripe_id = sa.Column(sa.String, nullable=True)
    user = sa.orm.relationship("User", back_populates="payment", lazy="noload")


class Doorevent(Base):
    __tablename__ = "door_event"

    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), primary_key=True)
    active = sa.orm.column_property(sa.func.coalesce(True))
    created_at = sa.Column(
        sa.DateTime,
        nullable=False,
        default=sa.func.current_timestamp(),
        primary_key=True,
    )


class LockTable(Base):
    __tablename__ = "lock_table"

    name = sa.Column(sa.String, primary_key=True)
    ran_at = sa.Column(sa.DateTime, nullable=False, default=utcnow())
