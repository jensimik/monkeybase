import datetime

from . import crud, models


async def generate_slots(db):
    products = await crud.products.get_multi(db, models.Product.slot_limit > 0)
    for product in products:
        member_count = await crud.member.count(
            db,
            models.Member.product_id == product.id,
            models.Member.active == True,
        )
        slot_count = await crud.slot.count(
            db,
            models.Slot.product_id == product.id,
            models.Slot.reserved_until >= datetime.datetime.utcnow(),
        )
        total = member_count + slot_count
        available = product.slot_limit - total
        if available > 0:
            # we have possibility to release more slots now

            # first check if any on waiting list
            # and get them by ascending order they added to waiting list
            waitings = await crud.waiting_list.get_multi(
                db,
                models.WaitingList.product_id == product.id,
                order_by=[models.WaitingList.created_at.asc()],
                limit=available,
            )
            for waiting in waitings:
                slot = await crud.slot.create(
                    db,
                    obj_in={
                        "product_id": product.id,
                        "user_id": waiting.user_id,
                        "reserved_until": datetime.datetime.utcnow()
                        + datetime.timedelta(days=2),
                    },
                )
                # disable this person from the waitinglist as
                # the person now got a slot/chance to sign up
                await crud.waiting_list.remove(db, models.WaitingList.id == waiting.id)
                # TODO: send a email that you now have a slot to sign up
                available -= 1
                if available == 0:
                    break
        # if still have more available then create open slots
        # without any user_id assigned
        if available > 0:
            for _ in range(available):
                await crud.slot.create(
                    db,
                    obj_in={
                        "product_id": product.id,
                        "reserved_until": datetime.datetime.utcnow()
                        + datetime.timedelta(days=2),
                    },
                )
