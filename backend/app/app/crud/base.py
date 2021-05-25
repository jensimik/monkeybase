import sqlalchemy as sa
from loguru import logger
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
        self,
        db: AsyncSession,
        *args,
        options: List[Any] = [],
        only_active: Optional[bool] = True,
        order_by: Optional[List[sa.sql.elements.UnaryExpression]] = [],
        limit: Optional[bool] = None,
        for_update: Optional[bool] = None,
        skip_locked: Optional[bool] = True,
    ) -> Optional[ModelType]:
        query = sa.select(self.model)
        if only_active:
            query = query.where(self.model.active == True, *args)
        else:
            query = query.where(*args)
        if options:
            query = query.options(*options)
        if order_by:
            query = query.order_by(*order_by)
        if limit:
            query = query.limit(1)
        if for_update:
            query = query.with_for_update(skip_locked=skip_locked)
        return (await db.execute(query)).scalar_one_or_none()

    def _get_multi_sql(
        self,
        *args,
        join: Optional[List] = [],
        options: Optional[List] = [],
        order_by: Optional[List[sa.sql.elements.UnaryExpression]] = [],
        only_active: Optional[bool] = True,
    ):
        query = sa.select(self.model)
        if join:
            query = query.join(*join)
        if only_active:
            query = query.where(self.model.active == True, *args)
        else:
            query = query.where(*args)
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
        only_active: Optional[bool] = True,
    ) -> List[ModelType]:
        query = self._get_multi_sql(
            *args,
            join=join,
            options=options,
            order_by=order_by,
            only_active=only_active,
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
        only_active: Optional[bool] = True,
    ) -> List[ModelType]:
        query = self._get_multi_sql(
            *args,
            join=join,
            options=options,
            order_by=order_by,
            only_active=only_active,
        )
        items = await select_page(db, query, page=page, per_page=per_page)
        return {
            "items": items,
            "next": items.paging.bookmark_next if items.paging.has_next else "",
            "has_next": items.paging.has_next,
        }

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        query = (
            sa.insert(self.model)
            .values(**obj_in.dict(exclude_unset=True))
            .returning(self.model)
        )
        return (await db.execute(query)).scalar_one()

    async def update(
        self,
        db: AsyncSession,
        *args,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        multi: Optional[bool] = False,
        only_active: Optional[bool] = True,
    ) -> ModelType:
        logger.info(obj_in)
        upd_dict = (
            obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        )
        query = sa.update(self.model).values(**upd_dict)
        if only_active:
            query = query.where(model.active == True, *args)
        else:
            query = query.where(*args)
        query = query.returning(self.model)
        res = await db.execute(query)
        # TODO: returning in sqlalchemy doesnt seem to work currently on ORM objects?
        # so for now just select the updated objects again and return them
        if multi:
            return await self.get_multi(db, *args, only_active=only_active)
        return await self.get(db, *args, only_active=only_active)

        # obj_data = jsonable_encoder(db_obj)
        # if isinstance(obj_in, dict):
        #     update_data = obj_in
        # else:
        #     update_data = obj_in.dict(exclude_unset=True)
        # for field in obj_data:
        #     if field in update_data:
        #         setattr(db_obj, field, update_data[field])
        # db.add(db_obj)
        # return db_obj

    async def remove(self, db: AsyncSession, *args, actual_delete=False) -> ModelType:
        if actual_delete:
            query = sa.delete(self.model).where(*args).returning(self.model)
            return (await db.execute(query)).scalar_one_or_none()
        # just set obj to inactive
        query = sa.update(self.model).where(*args).values({self.model.active: False})
        await db.execute(query)
