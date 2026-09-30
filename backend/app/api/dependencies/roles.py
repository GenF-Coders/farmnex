"""Role checks (FIX_PLAN F3).

Use in a route to let only some roles in; everyone else gets 403:

    @router.post("", dependencies=[Depends(require_roles("ADMIN", "SUPER_ADMIN"))])

or, when the route also needs the user:

    current_user: User = Depends(require_roles("FARMER", "VENDOR"))

Role names are the ones seeded in `app/main.py` (FARMER, BUYER, ADMIN, ...). Ownership checks
("is this row yours?") still belong in the service — a role check alone is never enough.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status

from app.api.dependencies.current_user import get_current_user
from app.models.user import User


def require_roles(*roles: str) -> Callable[..., Awaitable[User]]:
    """A dependency that returns the logged-in user if their role is one of `roles`, else 403."""
    if not roles:
        raise ValueError("require_roles() needs at least one role name.")
    allowed = frozenset(role.upper() for role in roles)

    async def _check(user: User = Depends(get_current_user)) -> User:
        role_name = user.role.name.upper() if user.role is not None else None
        if role_name not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed for your role.",
            )
        return user

    return _check
