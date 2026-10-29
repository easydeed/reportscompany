from fastapi import HTTPException, Request
from ..db import db_conn


#: The role on `account_users` that runs a company account (0007: "OWNER=full
#: control, MEMBER=read/write"). For a title company, MEMBER is read-only: the
#: company's admin actions move seats, sign reps out and send email in the
#: company's name.
COMPANY_ADMIN_ROLE = "OWNER"


def get_company_member(request: Request) -> dict:
    """
    Any user on a TITLE_COMPANY account: the read-only company views.

    Reads account_id from request.state (set by AuthContextMiddleware) and
    checks `accounts.account_type`, then the user's own role on that account
    in `account_users` (D-280). Returns user_info augmented with
    `company_account_id` and `is_company_admin`.

    Raises 401 if not authenticated, 403 if the account is not a title company
    or the user is not on it.
    """
    user_info = getattr(request.state, "user", None)
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")

    account_id = user_info.get("account_id") or getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # The middleware fills `id` only when it could match the token's user to
    # this account. Without one there is nobody to look up, and nobody is an
    # admin: fail closed.
    user_id = user_info.get("id")

    with db_conn() as (conn, cur):
        cur.execute(
            """
            SELECT a.account_type,
                   (SELECT au.role FROM account_users au
                     WHERE au.account_id = a.id AND au.user_id = %s::uuid
                     LIMIT 1)
              FROM accounts a
             WHERE a.id = %s::uuid
            """,
            (user_id, account_id),
        )
        row = cur.fetchone()

    if not row or row[0] != "TITLE_COMPANY":
        raise HTTPException(status_code=403, detail="Title Company accounts only")
    role = row[1]
    if role is None:
        raise HTTPException(status_code=403, detail="You are not a user on this company account")

    return {
        **user_info,
        "company_account_id": account_id,
        "company_role": role,
        "is_company_admin": role == COMPANY_ADMIN_ROLE,
    }


def get_company_admin(request: Request) -> dict:
    """
    The company's admin: the actions that change it — inviting and replacing
    reps, cancelling invites, resending invites, and the company brand.

    D-280: this used to check only that the ACCOUNT was a title company, so
    any user on the account could reassign a rep's seat, which signs that rep
    out for good. Now the user's own role on the account must be
    COMPANY_ADMIN_ROLE. Raises 403 otherwise, saying who can.
    """
    member = get_company_member(request)
    if not member["is_company_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only your company's admin can do this. You can see everything here, but not change it.",
        )
    return member
