import sqlalchemy as sa
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        query = sa.select(self.model).where(self.model.id == id)
        return (await db.execute(query)).scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *args,
        skip: int = 0,
        limit: int = 100,
        join: list = [],
        options: list = [],
        order_by: Optional[sa.sql.elements.UnaryExpression] = None,
    ) -> List[ModelType]:
        query = sa.select(self.model)
        if join:
            query = query.join(*join)
        query = query.where(self.model.active == True, *args)
        if options:
            query = query.options(*options)
        query = query.order_by(order_by).offset(skip).limit(limit)
        # query = query.order
        #     sa.select(self.model)
        #     .join(*join)
        #     .where(self.model.active == True, *args)
        #     .options(*options)
        #     .order_by(order_by)
        #     .offset(skip)
        #     .limit(limit)
        # )
        return (await db.execute(query)).scalars().all()

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        query = sa.insert(self.model).values(**obj_in_data).returning(self.model)
        return (await db.execute(query)).scalar_one()

    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, id: int) -> ModelType:
        query = sa.delete(self.model).where(self.model.id == id).returning(self.model)
        return (await db.execute(query)).scalar_one_or_none()
