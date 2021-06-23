import pytest
from .. import crud, models


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


async def test_delete(async_db):
    user = await crud.user.get(async_db, models.User.id == 1)
    assert user is not None

    # single remove
    await crud.user.remove(async_db, models.User.id == 1)

    user = await crud.user.get(async_db, models.User.id == 1)

    assert user is None

    user = await crud.user.get(async_db, models.User.id == 1, only_active=False)

    assert user is not None

    # multi remove
    await crud.user.remove(async_db, models.User.id.in_([2, 3, 4]))
    count = await crud.user.count(async_db, models.User.id.in_([2, 3, 4]))
    assert count == 0

    users = await crud.user.get_multi(async_db, models.User.id.in_([2, 3, 4]))
    assert len(users) == 0

    users = await crud.user.get_multi(
        async_db, models.User.id.in_([2, 3, 4]), only_active=False
    )
    assert len(users) == 3


async def test_count(async_db):
    count = await crud.user.count(async_db, models.User.id.in_([1, 2, 3, 4, 5]))

    assert count == 5
