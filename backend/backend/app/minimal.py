import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from core.config import settings

Base = declarative_base()
engine = sa.create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True, future=True)
Session = sa.orm.sessionmaker(bind=engine)


class A(Base):
    __tablename__ = "a"

    id = sa.Column(sa.Integer, sa.Identity(start=1, increment=1), primary_key=True)
    obj_type = sa.Column(sa.String)

    __mapper_args__ = {"polymorphic_identity": "a", "polymorphic_on": obj_type}


class B(A):
    name = sa.Column(sa.String)

    __mapper_args__ = {"polymorphic_identity": "b"}


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    session = Session()

    q = sa.insert(B).values({"name": "b"})
    session.execute(q)
    # INSERT INTO a (name) VALUES (%(name)s) RETURNING a.id
    # would expect obj_type = "b" would be set too?

    q = sa.future.select(B).from_statement(
        sa.update(B).values({"name": "c"}).where(B.name == "b").returning(B)
    )
    b = session.execute(q).scalar_one()
    # TypeError: 'sqlalchemy.cimmutabledict.immutabledict' object does not support item assignment
