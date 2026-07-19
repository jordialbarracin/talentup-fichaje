"""TalentUP Fichaje — Reusable async pagination helper."""
from math import ceil
from typing import Any, Callable, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


async def paginate(
    db: AsyncSession,
    query: Select,
    page: int,
    limit: int,
    *,
    item_transform: Optional[Callable[[Any], Any]] = None,
    count_column: Any = None,
) -> dict:
    """
    Apply offset/limit pagination to a SQLAlchemy select and return a
    standardized page envelope.

    Args:
        db: async SQLAlchemy session.
        query: the select statement to paginate (already filtered/ordered).
        page: 1-based page number.
        limit: items per page.
        item_transform: optional callable applied to each raw item before
            placing it in the `items` list.
        count_column: optional column/Star to count.

    Returns:
        {"items": [...], "total": N, "page": page, "limit": limit, "pages": ceil(N/limit)}
    """
    if page < 1:
        page = 1
    if limit < 1:
        limit = 1

    # Count total matching rows using a wrapped subquery to avoid cartesian products.
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * limit
    paginated_query = query.offset(offset).limit(limit)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    if item_transform:
        items = [item_transform(item) for item in items]

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": int(ceil(total / limit)) if limit else 1,
    }
