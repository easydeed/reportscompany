from fastapi import HTTPException, Request
from ..db import db_conn


def get_company_admin(request: Request) -> dict:
    """
    Dependency that verifies the current user belongs to a TITLE_COMPANY account.

    Reads account_id from request.state (set by AuthContextMiddleware),
    then checks accounts.account_type in the DB.

    Returns user_info dict augmented with company_account_id.
    Raises 401 if not authenticated, 403 if not a company admin.
    """
    user_info = getattr(request.state, "user", None)
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")

    account_id = user_info.get("account_id") or getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    with db_conn() as (conn, cur):
        cur.execute(
            "SELECT account_type FROM accounts WHERE id = %s::uuid",
            (account_id,),
        )
        row = cur.fetchone()

    if not row or row[0] != "TITLE_COMPANY":
        raise HTTPException(status_code=403, detail="Title Company admin only")

    return {**user_info, "company_account_id": account_id}
