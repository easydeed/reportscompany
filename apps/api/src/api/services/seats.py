"""
Rep seats for title companies (migration 0060).

SEATS ARE REP SEATS. A company pays for its reps; agents take no seat, stay
`sponsored_free`, and upgrade themselves. COMPLIANCE: giving sponsored agents
more than the Free plan's limits is a thing of value from a title company to a
referral source and needs a compliance check before anyone builds it. Nothing
in this module changes an agent's plan — reassignment moves an agent's sponsor
and leaves the plan exactly as it was.

The model, in one place:

  * `accounts.rep_seats` — the company's seat count. NULL: not on seats, and
    nothing is enforced (how every company behaved before seats). Set only by
    the platform admin, because companies are billed outside the app.
  * `rep_seat_assignments` — one row per period a rep holds a seat. Open rows
    are seats held. A pending invite holds its seat from the moment it is sent,
    and an expired one keeps holding it until it is cancelled.
  * Every operation that changes who holds a seat first locks the company's
    `accounts` row (`_lock_company`), so two invites racing for the last seat
    are serialised: the second waits, then counts the first's committed row.

Isolation: every function takes the CALLER'S company id and puts it in the
predicate of every rep it touches; a rep id from another company is
`SeatNotFound`, never a read. The app connects as a superuser (D-274), so these
predicates are the isolation, and test_rep_seats.py proves them cross-tenant.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

#: The window for an idle seat: a joined rep none of whose agents finished a
#: market or property report in this many days.
IDLE_DAYS = 30


class SeatsFull(Exception):
    """Every seat the company has is held (pending invites included)."""

    def __init__(self, total: int, held: int):
        self.total, self.held = total, held
        super().__init__(
            f"All {total} rep seat{'s' if total != 1 else ''} are in use "
            f"({held} held, pending invites included). Cancel a pending invite "
            f"or reassign a seat, or ask us for more seats.")


class SeatNotFound(LookupError):
    """The rep is not this company's, or holds no seat."""


class SeatConflict(Exception):
    """The operation does not apply to the rep in its current state."""


# ── reads ────────────────────────────────────────────────────────────────────

def _lock_company(cur, company_id: str) -> Optional[int]:
    """Lock the company row; return its seat count (None = not on seats)."""
    cur.execute(
        """
        SELECT rep_seats FROM accounts
         WHERE id = %s::uuid AND account_type = 'TITLE_COMPANY'
           FOR UPDATE
        """,
        (company_id,),
    )
    row = cur.fetchone()
    if not row:
        raise SeatNotFound("not a title company")
    return row[0]


def held_count(cur, company_id: str) -> int:
    cur.execute(
        """
        SELECT COUNT(*) FROM rep_seat_assignments
         WHERE company_account_id = %s::uuid AND ended_at IS NULL
        """,
        (company_id,),
    )
    return cur.fetchone()[0]


def _seat_holders(cur, company_id: str) -> List[Dict[str, Any]]:
    """Every open seat with its rep's join state and 30-day activity."""
    cur.execute(
        f"""
        SELECT s.rep_account_id::text AS rep_id,
               (u.email_verified AND u.password_hash IS NOT NULL) AS joined,
               EXISTS (
                 SELECT 1 FROM report_generations rg
                   JOIN accounts ag ON ag.id = rg.account_id
                  WHERE ag.sponsor_account_id = s.rep_account_id
                    AND rg.status = 'completed'
                    AND rg.generated_at >= NOW() - INTERVAL '{IDLE_DAYS} days'
               ) OR EXISTS (
                 -- `complete`, not `completed`: the two report tables spell
                 -- "finished" differently, and matching one spelling on both
                 -- would count every property report as not finished.
                 SELECT 1 FROM property_reports pr
                   JOIN accounts ag ON ag.id = pr.account_id
                  WHERE ag.sponsor_account_id = s.rep_account_id
                    AND pr.status = 'complete'
                    AND pr.created_at >= NOW() - INTERVAL '{IDLE_DAYS} days'
               ) AS active_30d
          FROM rep_seat_assignments s
          JOIN accounts r ON r.id = s.rep_account_id
                         AND r.parent_account_id = s.company_account_id
          LEFT JOIN LATERAL (
              SELECT u2.email_verified, u2.password_hash
                FROM account_users au JOIN users u2 ON u2.id = au.user_id
               WHERE au.account_id = s.rep_account_id AND au.role = 'OWNER'
               LIMIT 1
          ) u ON true
         WHERE s.company_account_id = %s::uuid AND s.ended_at IS NULL
        """,
        (company_id,),
    )
    return [
        {"rep_id": r[0], "joined": bool(r[1]), "idle": bool(r[1]) and not r[2]}
        for r in cur.fetchall()
    ]


def idle_rep_ids(cur, company_id: str) -> set:
    """Joined reps holding a seat whose agents finished no market or property
    report in `IDLE_DAYS` days. A rep with no agents is idle. A pending invite
    is counted as pending, not idle: nobody has had the chance to use it."""
    return {h["rep_id"] for h in _seat_holders(cur, company_id) if h["idle"]}


def seat_summary(cur, company_id: str) -> Optional[Dict[str, Any]]:
    """`{total, held, open, pending, idle}`, or None when not on seats."""
    cur.execute(
        "SELECT rep_seats FROM accounts WHERE id = %s::uuid AND account_type = 'TITLE_COMPANY'",
        (company_id,),
    )
    row = cur.fetchone()
    if not row or row[0] is None:
        return None
    holders = _seat_holders(cur, company_id)
    held = len(holders)
    return {
        "total": row[0],
        "held": held,
        "open": max(row[0] - held, 0),
        "pending": sum(1 for h in holders if not h["joined"]),
        "idle": sum(1 for h in holders if h["idle"]),
    }


def seat_history(cur, company_id: str) -> List[Dict[str, Any]]:
    """Every seat period, newest first: who held it, until when, and why not
    any more."""
    cur.execute(
        """
        SELECT s.rep_account_id::text, r.name, s.started_at, s.ended_at,
               s.ended_reason, s.successor_rep_account_id::text, succ.name,
               s.agents_moved
          FROM rep_seat_assignments s
          JOIN accounts r ON r.id = s.rep_account_id
          LEFT JOIN accounts succ ON succ.id = s.successor_rep_account_id
         WHERE s.company_account_id = %s::uuid
         ORDER BY COALESCE(s.ended_at, s.started_at) DESC, s.started_at DESC
        """,
        (company_id,),
    )
    return [
        {
            "rep_id": r[0], "rep_name": r[1],
            "started_at": r[2].isoformat() if r[2] else None,
            "ended_at": r[3].isoformat() if r[3] else None,
            "ended_reason": r[4],
            "successor_rep_id": r[5], "successor_name": r[6],
            "agents_moved": r[7],
        }
        for r in cur.fetchall()
    ]


#: The plan every agent a rep invites starts on (`invite_service`), and stays
#: on unless they upgrade themselves. Agents take no seat.
AGENT_PLAN = "sponsored_free"


def agent_plan(cur) -> Optional[Dict[str, Any]]:
    """`{plan_name, market_reports, schedules, property_reports}` for the
    agents' plan, read from `plans` (never typed in). A limit that is unset or
    not a plain number is None, and the page drops it. None when the plan row
    is missing."""
    cur.execute(
        """
        SELECT plan_name, market_reports_limit, schedules_limit, property_reports_per_month
          FROM plans WHERE plan_slug = %s
        """,
        (AGENT_PLAN,),
    )
    row = cur.fetchone()
    if not row:
        return None
    ok = lambda v: v if isinstance(v, int) and 0 < v < 10000 else None  # noqa: E731
    return {"plan_name": row[0], "market_reports": ok(row[1]),
            "schedules": ok(row[2]), "property_reports": ok(row[3])}


# ── writes ───────────────────────────────────────────────────────────────────

def reserve_seat(cur, company_id: str) -> None:
    """Lock the company and refuse if every seat is held. Call BEFORE creating
    the rep, in the same transaction, and `open_seat` after."""
    total = _lock_company(cur, company_id)
    if total is None:
        return
    held = held_count(cur, company_id)
    if held >= total:
        raise SeatsFull(total, held)


def open_seat(cur, company_id: str, rep_account_id: str) -> None:
    cur.execute(
        """
        INSERT INTO rep_seat_assignments (company_account_id, rep_account_id)
        SELECT %s::uuid, a.id FROM accounts a
         WHERE a.id = %s::uuid AND a.parent_account_id = %s::uuid
           AND a.account_type = 'INDUSTRY_AFFILIATE'
        """,
        (company_id, rep_account_id, company_id),
    )
    if cur.rowcount != 1:
        raise SeatNotFound("rep is not under this company")


def _open_seat_rep(cur, company_id: str, rep_account_id: str) -> Dict[str, Any]:
    """The rep, if it is this company's and holds a seat; else SeatNotFound."""
    cur.execute(
        """
        SELECT a.id::text, a.name, s.id::text,
               (u.email_verified AND u.password_hash IS NOT NULL) AS joined
          FROM accounts a
          JOIN rep_seat_assignments s ON s.rep_account_id = a.id
                                     AND s.company_account_id = %s::uuid
                                     AND s.ended_at IS NULL
          LEFT JOIN LATERAL (
              SELECT u2.email_verified, u2.password_hash
                FROM account_users au JOIN users u2 ON u2.id = au.user_id
               WHERE au.account_id = a.id AND au.role = 'OWNER'
               LIMIT 1
          ) u ON true
         WHERE a.id = %s::uuid AND a.parent_account_id = %s::uuid
           AND a.account_type = 'INDUSTRY_AFFILIATE'
        """,
        (company_id, rep_account_id, company_id),
    )
    row = cur.fetchone()
    if not row:
        raise SeatNotFound("rep not found under your company, or holds no seat")
    return {"id": row[0], "name": row[1], "seat_id": row[2], "joined": bool(row[3])}


def _switch_off(cur, account_id: str) -> None:
    """The same three writes D-273 made for a deactivated agent: sign-in and
    sends refused (`users.is_active`), unused invite links spent, and the
    account flag the admin views read."""
    cur.execute("UPDATE users SET is_active = FALSE WHERE account_id = %s::uuid", (account_id,))
    cur.execute(
        "UPDATE signup_tokens SET used = TRUE WHERE account_id = %s::uuid AND used = FALSE",
        (account_id,),
    )
    cur.execute("UPDATE accounts SET is_active = FALSE WHERE id = %s::uuid", (account_id,))


def reassign_seat(
    cur,
    *,
    company_id: str,
    from_rep_id: str,
    create_successor,
    agents_to_rep_id: Optional[str] = None,
    actor_user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Move rep A's seat to a new rep B, in the caller's transaction.

    `create_successor(cur)` creates B (an invite) and returns its account id;
    the caller owns the invite details. Then:

      * A's seat row closes as 'reassigned', naming B, and B's opens. The seat
        count does not move, so no cap check: the company holds as many seats
        after as before.
      * A's agents move — to B by default ("agents move with the seat"), or to
        `agents_to_rep_id`, another rep of THIS company holding a seat. Only
        `sponsor_account_id` changes; every agent keeps its plan.
      * A's BOOK goes where the agents go (`hand_over_book`): A's scheduled
        sends, the contacts and groups they resolve recipients from, and
        copies of A's unsubscribes. Otherwise the agents stop getting their
        reports the day their rep changes and nobody is told.
      * A is switched off.

    Returns the moved agents' ids, names and owner emails, for the notices.
    """
    _lock_company(cur, company_id)
    leaving = _open_seat_rep(cur, company_id, from_rep_id)
    target = None
    if agents_to_rep_id:
        if agents_to_rep_id == from_rep_id:
            raise SeatConflict("agents cannot be moved to the rep who is leaving")
        target = _open_seat_rep(cur, company_id, agents_to_rep_id)

    successor_id = create_successor(cur)
    destination = target["id"] if target else successor_id

    cur.execute(
        """
        UPDATE accounts SET sponsor_account_id = %s::uuid, updated_at = NOW()
         WHERE sponsor_account_id = %s::uuid
        RETURNING id::text, name
        """,
        (destination, from_rep_id),
    )
    moved = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
    schedules_moved = hand_over_book(cur, from_account_id=from_rep_id, to_account_id=destination)

    cur.execute(
        """
        UPDATE rep_seat_assignments
           SET ended_at = NOW(), ended_reason = 'reassigned',
               successor_rep_account_id = %s::uuid,
               ended_by_user_id = %s::uuid, agents_moved = %s,
               book_to_account_id = %s::uuid, schedules_moved = %s
         WHERE id = %s::uuid AND ended_at IS NULL
        """,
        (successor_id, actor_user_id, len(moved), destination, schedules_moved,
         leaving["seat_id"]),
    )
    open_seat(cur, company_id, successor_id)
    _switch_off(cur, from_rep_id)

    recipients = []
    if moved:
        cur.execute(
            """
            SELECT u.email, COALESCE(u.first_name, ''), a.id::text
              FROM accounts a
              JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
              JOIN users u ON u.id = au.user_id
             WHERE a.id = ANY(%s::uuid[]) AND u.is_active
            """,
            ([m["id"] for m in moved],),
        )
        recipients = [{"email": r[0], "first_name": r[1], "account_id": r[2]}
                      for r in cur.fetchall()]

    return {
        "from_rep": {"id": leaving["id"], "name": leaving["name"]},
        "successor_rep_id": successor_id,
        "agents_to_rep_id": destination,
        "agents_moved": moved,
        "schedules_moved": schedules_moved,
        "notice_recipients": recipients,
    }


def hand_over_book(cur, *, from_account_id: str, to_account_id: str) -> int:
    """Move a leaving rep's scheduled sends, and what they depend on, to the
    account taking over their agents. Returns how many schedules moved.

    WHAT HAS TO MOVE TOGETHER. The worker resolves a schedule's recipients
    against the schedule's OWN account (`tasks.resolve_recipients_to_emails`):
    a contact or a group is read `WHERE account_id = <schedule's account>`, and
    an agent recipient must be sponsored by it. Moving the schedules alone
    would leave every contact and group recipient unresolvable — the schedule
    would run and send to nobody. So the contacts, the groups and the group
    memberships move with them (ids unchanged, so every reference still
    holds), and agent recipients resolve because the agents moved first.

    AND THE UNSUBSCRIBES, COPIED. Suppressions are per account
    (`email_suppressions.account_id`, read by worker/email/send.py). A
    recipient who opted out of the leaving rep's emails must not start getting
    the same emails under a new name. Copied rather than moved: the leaving
    rep's record of who opted out stays theirs.

    Schedules keep their timing, history and `active` flag. They send once the
    receiving account can send (`schedules_tick.account_can_send`): at once
    for an existing rep, and from when a newly invited rep accepts and
    confirms their address — the D-019 rule that nothing goes out in the name
    of an unconfirmed address.
    """
    cur.execute(
        "UPDATE schedules SET account_id = %s::uuid WHERE account_id = %s::uuid RETURNING id",
        (to_account_id, from_account_id),
    )
    moved = len(cur.fetchall())
    for table in ("contacts", "contact_groups", "contact_group_members"):
        cur.execute(
            f"UPDATE {table} SET account_id = %s::uuid WHERE account_id = %s::uuid",
            (to_account_id, from_account_id),
        )
    cur.execute(
        """
        INSERT INTO email_suppressions (account_id, email, reason)
        SELECT %s::uuid, email, reason FROM email_suppressions WHERE account_id = %s::uuid
        ON CONFLICT (account_id, email) DO NOTHING
        """,
        (to_account_id, from_account_id),
    )
    return moved


def book_successors(cur, account_ids: List[str]) -> List[str]:
    """Every account a book was handed to from `account_ids`, transitively —
    A to B, then B to C if B's seat moved too. For the unsubscribe route: a
    link signed for A, clicked after the move, must stop the sends that are
    now B's."""
    if not account_ids:
        return []
    cur.execute(
        """
        WITH RECURSIVE chain(account_id) AS (
            SELECT book_to_account_id FROM rep_seat_assignments
             WHERE rep_account_id = ANY(%s::uuid[]) AND book_to_account_id IS NOT NULL
            UNION
            SELECT s.book_to_account_id FROM rep_seat_assignments s
              JOIN chain c ON s.rep_account_id = c.account_id
             WHERE s.book_to_account_id IS NOT NULL
        )
        SELECT account_id::text FROM chain
        """,
        (account_ids,),
    )
    return [r[0] for r in cur.fetchall() if r[0] not in account_ids]


def agent_emails_for(cur, company_id: str, rep_account_id: str) -> List[str]:
    """The active agents' owner emails under one of this company's reps — the
    addresses a reassignment will write to, for the sender check."""
    cur.execute(
        """
        SELECT u.email FROM accounts ag
          JOIN accounts rep ON rep.id = ag.sponsor_account_id
                           AND rep.parent_account_id = %s::uuid
          JOIN account_users au ON au.account_id = ag.id AND au.role = 'OWNER'
          JOIN users u ON u.id = au.user_id
         WHERE ag.sponsor_account_id = %s::uuid AND u.is_active
        """,
        (company_id, rep_account_id),
    )
    return [r[0] for r in cur.fetchall()]


def cancel_rep_invite(cur, *, company_id: str, rep_id: str,
                      actor_user_id: Optional[str] = None) -> None:
    """Withdraw a pending rep invite and free its seat.

    Only for a rep who has not joined — a joined rep's seat moves by
    reassignment, which says where their agents go. A pending rep has had no
    way to invite agents, and one that somehow has them is refused rather than
    leaving them under a switched-off sponsor.
    """
    _lock_company(cur, company_id)
    rep = _open_seat_rep(cur, company_id, rep_id)
    if rep["joined"]:
        raise SeatConflict("this rep has joined; reassign their seat instead")
    cur.execute("SELECT COUNT(*) FROM accounts WHERE sponsor_account_id = %s::uuid", (rep_id,))
    if cur.fetchone()[0]:
        raise SeatConflict("this rep has agents; reassign their seat instead")
    cur.execute(
        """
        UPDATE rep_seat_assignments
           SET ended_at = NOW(), ended_reason = 'invite_cancelled',
               ended_by_user_id = %s::uuid
         WHERE id = %s::uuid AND ended_at IS NULL
        """,
        (actor_user_id, rep["seat_id"]),
    )
    _switch_off(cur, rep_id)


def set_seat_count(cur, company_id: str, rep_seats: Optional[int]) -> Dict[str, Any]:
    """The platform admin's setter. Refuses a count below the seats already
    held: that would leave reps holding seats the company does not have."""
    _lock_company(cur, company_id)
    held = held_count(cur, company_id)
    if rep_seats is not None and rep_seats < held:
        raise SeatConflict(
            f"{held} seats are held; release or cancel some before setting {rep_seats}")
    cur.execute(
        "UPDATE accounts SET rep_seats = %s, updated_at = NOW() WHERE id = %s::uuid",
        (rep_seats, company_id),
    )
    return {"rep_seats": rep_seats, "held": held}
