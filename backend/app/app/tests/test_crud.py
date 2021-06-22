from .. import crud, models


async def test_get(async_db):
    user = await crud.user.get(async_db, models.User.id == 1)
    assert user.id == 1

    unknown = await crud.user.get(async_db, models.User.id == 999999)
    assert unknown is None


async def test_get_multi(async_db):
    users = await crud.user.get_multi(async_db, models.User.id.in_([1, 2, 3]))
    assert len(users) == 3


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


async def test_update(async_db, fake_name):
    user = await crud.user.get(async_db, models.User.id == 1)

    orig_name = user.name

    user = await crud.user.update(
        async_db, models.User.id == user.id, obj_in={"name": fake_name}
    )

    assert orig_name != user.name
