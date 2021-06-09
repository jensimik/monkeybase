import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as sa_pg

from .db import Base
from .utils.models_utils import (
    DoorAccessEnum,
    StripeStatusEnum,
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
    door_id = sa.Column(sa.String, nullable=True, index=True)
    stripe_customer_id = sa.Column(sa.String, nullable=True)
    member = sa.orm.relationship("Member", back_populates="user", lazy="noload")
    webauthn = sa.orm.relationship("Webauthn", back_populates="user", lazy="noload")
    slot = sa.orm.relationship("Slot", back_populates="user", lazy="noload")
    waiting_list = sa.orm.relationship(
        "WaitingList", back_populates="user", lazy="noload"
    )


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
    product_id = sa.Column(sa.Integer, sa.ForeignKey("product.id"), primary_key=True)
    date_start = sa.Column(sa.Date, nullable=False)
    date_end = sa.Column(sa.Date, nullable=False)
    active = sa.orm.column_property(date_end > sa.func.now())
    user = sa.orm.relationship("User", back_populates="member", lazy="noload")
    product = sa.orm.relationship("Product", back_populates="member", lazy="noload")
    stripe_id = sa.Column(sa.String)


class Product(TimestampableMixin, Base):
    __tablename__ = "product"

    id = sa.Column(sa.Integer, sa.Identity(start=1, increment=1), primary_key=True)
    obj_type = sa.Column(sa.String, index=True)
    name = sa.Column(sa.String, nullable=False)
    name_short = sa.Column(
        sa.String, nullable=False
    )  # short version of name, for credit card statement, and other places
    description = sa.Column(sa.Text)
    active = sa.Column(sa.Boolean, default=True, nullable=False)
    slot_limit = sa.Column(sa.Integer, default=0, nullable=False)
    price = sa.Column(sa.Integer, default=0, nullable=False)  # price in cents
    member = sa.orm.relationship("Member", back_populates="product", lazy="noload")
    slot = sa.orm.relationship("Slot", back_populates="product", lazy="noload")
    waiting_list = sa.orm.relationship(
        "WaitingList", back_populates="product", lazy="noload"
    )

    __mapper_args__ = {"polymorphic_identity": "product", "polymorphic_on": obj_type}

    def send_welcome(self, user: User):
        pass


class MemberType(Product):
    """Model for membership"""

    door_access = sa.Column(sa_pg.ENUM(DoorAccessEnum), default=DoorAccessEnum.NOACCESS)

    __mapper_args__ = {
        "polymorphic_identity": "member_type",
        "polymorphic_load": "selectin",
    }


class Event(Product):
    date_signup_deadline = sa.Column(sa.DateTime)
    date_start = sa.Column(sa.DateTime)
    date_end = sa.Column(sa.DateTime)

    __mapper_args__ = {"polymorphic_identity": "event", "polymorphic_load": "selectin"}


class Slot(Base, TimestampableMixin):
    """model for available generic slots"""

    __tablename__ = "slot"

    id = sa.Column(sa.Integer, sa.Identity(start=1, increment=1), primary_key=True)
    active = sa.Column(sa.Boolean, default=True, nullable=False)
    key = sa.Column(sa_pg.UUID, nullable=False, default=gen_uuid())
    reserved_until = sa.Column(sa.DateTime, nullable=False, default=utcnow())
    stripe_id = sa.Column(sa.String)
    stripe_status = sa.Column(
        sa_pg.ENUM(StripeStatusEnum),
        nullable=False,
        default=StripeStatusEnum.NOT_AVAILABLE,
    )
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), nullable=True)
    product_id = sa.Column(sa.Integer, sa.ForeignKey("product.id"))
    user = sa.orm.relationship("User", back_populates="slot", lazy="noload")
    product = sa.orm.relationship("Product", back_populates="slot", lazy="noload")


class WaitingList(TimestampableMixin, Base):
    __tablename__ = "waiting_list"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True, index=True)
    active = sa.Column(sa.Boolean, default=False, nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), primary_key=True)
    user = sa.orm.relationship("User", back_populates="waiting_list", lazy="noload")
    product_id = sa.Column(sa.Integer, sa.ForeignKey("product.id"))
    product = sa.orm.relationship(
        "Product", back_populates="waiting_list", lazy="noload"
    )


class Doorevent(Base):
    __tablename__ = "door_event"

    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), primary_key=True)
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
