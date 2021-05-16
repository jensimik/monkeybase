import sqlalchemy as sa
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from .utils import select_page

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

    async def get(
        self, db: AsyncSession, id: Any, options: List[Any] = []
    ) -> Optional[ModelType]:
        query = sa.select(self.model).where(self.model.id == id)
        if options:
            query = query.options(*options)
        return (await db.execute(query)).scalar_one_or_none()

    def _get_multi_sql(
        self,
        *args,
        join: Optional[List] = [],
        options: Optional[List] = [],
        order_by: Optional[List[sa.sql.elements.UnaryExpression]] = [],
    ):
        query = sa.select(self.model)
        if join:
            query = query.join(*join)
        query = query.where(self.model.active == True, *args)
        if options:
            query = query.options(*options)
        if order_by:
            query = query.order_by(*order_by)
        else:
            # multi should always be ordered for keyset pagination to work
            query = query.order_by(self.model.id.asc())
        return query

    async def get_multi(
        self,
        db: AsyncSession,
        *args,
        join: Optional[List[Any]] = [],
        options: Optional[List[Any]] = [],
        order_by: Optional[List[sa.sql.elements.UnaryExpression]] = [],
    ) -> List[ModelType]:
        query = self._get_multi_sql(
            *args, join=join, options=options, order_by=order_by
        )
        return (await db.execute(query)).scalars().all()

    async def get_multi_page(
        self,
        db: AsyncSession,
        *args,
        join: Optional[List[Any]] = [],
        options: Optional[List[Any]] = [],
        per_page: Optional[int] = 100,
        page: Optional[str] = None,
        order_by: Optional[List[sa.sql.elements.UnaryExpression]] = [],
    ) -> List[ModelType]:
        query = self._get_multi_sql(
            *args, join=join, options=options, order_by=order_by
        )
        items = await select_page(db, query, page=page, per_page=per_page)
        return {
            "items": items,
            "next": items.paging.bookmark_next if items.paging.has_next else "",
            "has_next": items.paging.has_next,
        }

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
