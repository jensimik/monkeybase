import datetime

import pytest

from backend.app import crud, models


@pytest.mark.parametrize(
    "scoped_crud,model,id",
    [
        (crud.user, models.User, 1),
        (crud.product, models.Product, 1),
        (crud.event, models.Event, 3),
        (crud.member_type, models.MemberType, 1),
    ],
)
async def test_get(async_db, scoped_crud, model, id):
    obj = await scoped_crud.get(async_db, model.id == id)
    assert obj is not None
    assert isinstance(obj, model)
    assert obj.id == id

    unknown = await scoped_crud.get(async_db, model.id == 999999)
    assert unknown is None


@pytest.mark.parametrize(
    "scoped_crud,model,ids",
    [
        (crud.user, models.User, [1, 2, 3]),
        (crud.product, models.Product, [1]),
        (crud.event, models.Event, [3]),
        (crud.member_type, models.MemberType, [1, 2]),
    ],
)
async def test_get_multi(async_db, scoped_crud, model, ids):
    objs = await scoped_crud.get_multi(async_db, model.id.in_(ids))
    assert len(objs) == len(ids)


async def test_get_multi_page(async_db):
    page = await crud.user.get_multi_page(async_db, per_page=10)

    assert page["has_next"] is True
    assert isinstance(page["items"][0], models.User)
    assert len(page["items"]) == 10
    assert page["next"] == ">i:10"

    # try to get page2
    page2 = await crud.user.get_multi_page(async_db, per_page=10, page=page["next"])

    assert len(page2["items"]) == 10
    assert page["items"][0].id != page2["items"][0].id

    assert page2["next"] != page["next"]


@pytest.mark.parametrize(
    "scoped_crud,model,id",
    [
        (crud.user, models.User, 1),
        (crud.product, models.Product, 1),
        (crud.event, models.Event, 3),
        (crud.member_type, models.MemberType, 1),
    ],
)
async def test_update(async_db, fake_name, scoped_crud, model, id):
    obj = await scoped_crud.get(async_db, model.id == id)

    orig_name = obj.name

    obj = await scoped_crud.update(
        async_db, model.id == obj.id, obj_in={"name": fake_name}
    )

    assert orig_name != obj.name


@pytest.mark.parametrize(
    "scoped_crud,model,id,ids",
    [
        (crud.user, models.User, 1, [1, 2, 3]),
        (crud.product, models.Product, 1, [1]),
        (crud.event, models.Event, 3, [3]),
        (crud.member_type, models.MemberType, 1, [1, 2]),
    ],
)
async def test_delete(async_db, scoped_crud, model, id, ids):
    obj = await scoped_crud.get(async_db, model.id == id)
    assert obj is not None

    # single remove
    await scoped_crud.remove(async_db, model.id == id)

    obj = await scoped_crud.get(async_db, model.id == id)
    assert obj is None

    obj = await scoped_crud.get(async_db, model.id == id, only_active=False)

    assert obj is not None

    # multi remove
    await scoped_crud.remove(async_db, model.id.in_(ids))

    count = await scoped_crud.count(async_db, model.id.in_(ids))
    assert count == 0

    count = await scoped_crud.count(async_db, model.id.in_(ids))
    assert count == 0

    objs = await scoped_crud.get_multi(async_db, model.id.in_(ids))
    assert len(objs) == 0

    objs = await scoped_crud.get_multi(async_db, model.id.in_(ids), only_active=False)
    assert len(objs) == len(ids)


@pytest.mark.parametrize(
    "scoped_crud,model,ids",
    [
        (crud.user, models.User, [1, 2, 3]),
        (crud.product, models.Product, [1]),
        (crud.event, models.Event, [3]),
        (crud.member_type, models.MemberType, [1, 2]),
    ],
)
async def test_count(async_db, scoped_crud, model, ids):
    count = await scoped_crud.count(async_db, model.id.in_(ids))

    assert count == len(ids)


@pytest.mark.parametrize(
    "scoped_crud,model,obj_in",
    [
        (
            crud.user,
            models.User,
            {
                "name": "n",
                "email": "t@t.dk",
                "hashed_password": "h",
                "birthday": datetime.datetime.utcnow(),
            },
        ),
        (crud.event, models.Event, {"name": "e", "name_short": "e"}),
        (crud.member_type, models.MemberType, {"name": "mt", "name_short": "mt"}),
    ],
)
async def test_create(async_db, scoped_crud, model, obj_in):
    obj = await scoped_crud.create(async_db, obj_in=obj_in)

    assert isinstance(obj, model)
