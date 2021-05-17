import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as sa_pg
from sqlalchemy.ext.compiler import compiles


class utcnow(sa.sql.expression.FunctionElement):
    type = sa.DateTime()


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


class gen_uuid(sa.sql.expression.FunctionElement):
    type = sa_pg.UUID()


@compiles(gen_uuid, "postgresql")
def pg_uuid(element, compiler, **kw):
    return "uuid_generate_v4()"


class TimestampableMixin:
    """Allow a model to track its creation and update times"""

    created_at = sa.Column(sa.DateTime, nullable=False, default=utcnow())
    updated_at = sa.Column(
        sa.DateTime,
        nullable=False,
        server_default=utcnow(),
        onupdate=utcnow(),
    )
