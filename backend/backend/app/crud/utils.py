# type: ignore

from functools import partial

from loguru import logger
from sqlakeyset.columns import find_order_key, parse_ob_clause
from sqlakeyset.paging import Page, Paging, process_args, where_condition_for_page
from sqlakeyset.sqla import group_by_clauses

from ..db import AsyncSession


async def perform_paging(q, per_page, place, backwards, orm=True, s=None):
    column_descriptions = q.column_descriptions
    selectable = q

    order_cols = parse_ob_clause(selectable)
    if backwards:
        order_cols = [c.reversed for c in order_cols]
    mapped_ocols = [find_order_key(ocol, column_descriptions) for ocol in order_cols]

    clauses = [col.ob_clause for col in mapped_ocols]
    q = q.order_by(None).order_by(*clauses)

    extra_columns = [
        col.extra_column for col in mapped_ocols if col.extra_column is not None
    ]
    q = q.add_columns(*extra_columns)

    if place:
        dialect = getattr(s, "bind", s).dialect
        condition = where_condition_for_page(order_cols, place, dialect)
        # For aggregate queries, paging condition is applied *after*
        # aggregation. In SQL this means we need to use HAVING instead of
        # WHERE.
        groupby = group_by_clauses(selectable)
        if groupby is not None and len(groupby) > 0:
            q = q.having(condition)
        elif orm:
            q = q.filter(condition)
        else:
            q = q.where(condition)

    q = q.limit(per_page + 1)  # 1 extra to check if there's a further page
    selected = await s.execute(q)
    keys = list(selected.keys())
    keys = keys[: len(keys) - len(extra_columns)]
    rows = selected.scalars().all()
    return order_cols, mapped_ocols, extra_columns, rows, keys


async def core_get_page(s: AsyncSession, selectable, per_page, place, backwards):
    """Get a page from an SQLAlchemy Core selectable.

    :param s: :class:`sqlalchemy.engine.Connection` or
        :class:`sqlalchemy.orm.session.Session` to use to execute the query.
    :param selectable: The source selectable.
    :param per_page: Number of rows per page.
    :param place: Keyset representing the place after which to start the page.
    :param backwards: If ``True``, reverse pagination direction.
    :returns: :class:`Page`
    """
    # We need the result schema for the *original* query in order to properly
    # trim off our extra_columns. As far as I can tell, this is the only
    # way to get it without copy-pasting chunks of the sqlalchemy internals.
    # LIMIT 0 to minimize database load (though the fact that a round trip to
    # the DB has to happen at all is regrettable).
    result_type = await core_result_type(selectable, s)
    paging_result = await perform_paging(
        q=selectable,
        per_page=per_page,
        place=place,
        backwards=backwards,
        orm=False,
        s=s,
    )
    page = core_page_from_rows(
        paging_result, result_type, per_page, backwards, current_marker=place
    )
    return page


def core_page_from_rows(
    paging_result, result_type, page_size, backwards=False, current_marker=None
):
    """Turn a raw page of results for an SQLAlchemy Core query (as obtained by
    :func:`.core_get_page`) into a :class:`.Page` for external consumers."""
    ocols, mapped_ocols, extra_columns, rows, keys = paging_result

    make_row = partial(
        core_coerce_row, extra_columns=extra_columns, result_type=result_type
    )
    out_rows = [make_row(row) for row in rows]
    key_rows = [tuple(getattr(row, col.attr) for col in mapped_ocols) for row in rows]
    paging = Paging(
        out_rows, page_size, ocols, backwards, current_marker, markers=key_rows
    )

    page = Page(paging.rows, paging, keys=keys)
    return page


async def core_result_type(selectable, s):
    """Given a SQLAlchemy Core selectable and a connection/session, get the
    type constructor for the result row type."""
    result_proxy = await s.execute(selectable.limit(0))
    return result_proxy._row_getter


def core_coerce_row(row, extra_columns, result_type):
    """Trim off the extra columns and return as a correct-as-possible
    sqlalchemy Row."""
    if not extra_columns:
        return row
    return result_type(row[: len(row) - len(extra_columns)])


async def select_page(
    s: AsyncSession, selectable, per_page, after=False, before=False, page=None
):
    """Get a page of results from a SQLAlchemy Core selectable.

    Specify no more than one of the arguments ``page``, ``after`` or
    ``before``. If none of these are provided, the first page is returned.

    :param s: :class:`sqlalchemy.engine.Connection` or
        :class:`sqlalchemy.orm.session.Session` to use to execute the query.
    :param selectable: The source selectable.
    :param per_page: The (maximum) number of rows on the page.
    :type per_page: int, optional.
    :param page: a ``(keyset, backwards)`` pair or string bookmark describing
        the page to get.
    :param after: if provided, the page will consist of the rows immediately
        following the specified keyset.
    :param before: if provided, the page will consist of the rows immediately
        preceding the specified keyset.

    :returns: A :class:`Page` containing the requested rows and paging hooks
        to access surrounding pages.
    """
    place, backwards = process_args(after, before, page)

    return await core_get_page(s, selectable, per_page, place, backwards)
