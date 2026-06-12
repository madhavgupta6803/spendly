"""
tests/test_09-delete-expense.py

Tests for the Step 09 "Delete Expense" feature.

All test logic is derived exclusively from the feature spec
(.claude/specs/09-delete-expense.md).  The implementation is NOT read for
test logic.

Route under test:
  POST /expenses/<int:id>/delete — verify ownership, delete the row, redirect
                                   to /profile (auth required, POST only)

Template under test:
  templates/profile.html — each transaction row must contain an inline
  <form method="POST"> pointing at the delete URL, with an onsubmit confirm()
  guard.

Fixture strategy:
  - Reuses shared `app`, `client` fixtures from conftest.py (tmp-path-isolated
    SQLite DB, no seed data injected automatically).
  - Defines a local `auth_client` fixture that inserts a user directly and
    logs in via POST /login.
  - Defines a local `other_client` fixture for a second, independent user to
    test ownership enforcement.
  - Defines local DB helpers to insert expenses and query rows directly, so
    DB side effects can be verified without relying on the HTTP layer.
"""

import pytest
from werkzeug.security import generate_password_hash

from database.db import get_db


# ---------------------------------------------------------------------------
# Local fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_client(app, client):
    """
    A test client with an active session for 'owner@spendly.com'.
    The user is inserted directly into the DB to avoid coupling to /register.
    """
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Owner User", "owner@spendly.com", generate_password_hash("ownerpass1")),
    )
    conn.commit()
    conn.close()

    resp = client.post(
        "/login",
        data={"email": "owner@spendly.com", "password": "ownerpass1"},
        follow_redirects=False,
    )
    assert resp.status_code == 302, "Login must redirect on success"
    return client


@pytest.fixture
def other_client(app):
    """
    A separate test client logged in as a different user ('other@spendly.com').
    Used to verify that one user cannot delete another user's expense.
    """
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Other User", "other@spendly.com", generate_password_hash("otherpass1")),
    )
    conn.commit()
    conn.close()

    other = app.test_client()
    resp = other.post(
        "/login",
        data={"email": "other@spendly.com", "password": "otherpass1"},
        follow_redirects=False,
    )
    assert resp.status_code == 302, "Login must redirect on success"
    return other


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _get_csrf_token(client):
    """Extract the CSRF token stored in the client's session after login."""
    with client.session_transaction() as sess:
        return sess.get("csrf_token", "")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _insert_expense(email, amount=100.0, category="Food",
                    expense_date="2026-06-01", description="Test expense"):
    """
    Insert a single expense for the user identified by email.
    Returns the new expense's id.
    """
    conn = get_db()
    user = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()
    cursor = conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description)"
        " VALUES (?, ?, ?, ?, ?)",
        (user["id"], amount, category, expense_date, description),
    )
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return expense_id


def _fetch_expense_by_id(expense_id):
    """
    Return the expense row dict for the given id, or None if it doesn't exist.
    Used to verify DB side effects after a delete.
    """
    conn = get_db()
    row = conn.execute(
        "SELECT id, amount, category, date, description FROM expenses WHERE id = ?",
        (expense_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _count_expenses_for_email(email):
    """Return the total number of expense rows owned by the user with given email."""
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM expenses e "
        "JOIN users u ON u.id = e.user_id "
        "WHERE u.email = ?",
        (email,),
    ).fetchone()[0]
    conn.close()
    return count


# ---------------------------------------------------------------------------
# HTTP method guard — GET must return 405
# ---------------------------------------------------------------------------

class TestMethodGuard:
    def test_get_request_returns_405(self, auth_client):
        """
        The spec states the route is POST-only (methods=['POST']).
        A GET request must return 405 Method Not Allowed.
        """
        expense_id = _insert_expense("owner@spendly.com")
        response = auth_client.get(f"/expenses/{expense_id}/delete")
        assert response.status_code == 405, (
            "GET /expenses/<id>/delete must return 405 — route is POST-only"
        )

    def test_get_request_on_nonexistent_id_returns_405(self, auth_client):
        """
        Even for a non-existent id, a GET must return 405 before any
        existence/ownership check runs (Flask rejects the method first).
        """
        response = auth_client.get("/expenses/99999/delete")
        assert response.status_code == 405, (
            "GET /expenses/99999/delete must return 405 regardless of expense existence"
        )


# ---------------------------------------------------------------------------
# Auth guard — unauthenticated requests redirect to /login
# ---------------------------------------------------------------------------

class TestAuthGuard:
    def test_post_unauthenticated_redirects_to_login(self, client):
        """
        POSTing to the delete endpoint without a session must redirect to /login.
        No expense needs to exist; the auth check fires first.
        """
        response = client.post("/expenses/1/delete")
        assert response.status_code == 302, (
            "POST /expenses/<id>/delete without session must return 302"
        )
        assert "/login" in response.headers["Location"], (
            "Unauthenticated delete POST must redirect to /login"
        )

    def test_post_unauthenticated_with_valid_id_still_redirects(self, app, client):
        """
        Even when the expense actually exists, an unauthenticated request
        must redirect to /login — auth check must come before existence check.
        """
        # Insert a user and expense without logging in via client
        conn = get_db()
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Anon Owner", "anon@spendly.com", generate_password_hash("anonpass1")),
        )
        user_id = cursor.lastrowid
        exp_cursor = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            (user_id, 50.0, "Food", "2026-06-01", "Anon expense"),
        )
        expense_id = exp_cursor.lastrowid
        conn.commit()
        conn.close()

        response = client.post(f"/expenses/{expense_id}/delete")
        assert response.status_code == 302, (
            "POST to a real expense id without session must still return 302"
        )
        assert "/login" in response.headers["Location"], (
            "Unauthenticated delete must redirect to /login even for a real expense"
        )

        # Confirm the row was NOT deleted
        assert _fetch_expense_by_id(expense_id) is not None, (
            "Unauthenticated request must not delete the expense row"
        )


# ---------------------------------------------------------------------------
# Ownership guard — another user's expense returns 404
# ---------------------------------------------------------------------------

class TestOwnershipGuard:
    def test_post_other_users_expense_returns_404(self, auth_client, other_client):
        """
        When user B (other_client) POSTs to delete an expense owned by user A
        (auth_client / owner@spendly.com), the response must be 404.
        The spec states: use get_expense_by_id(id, session['user_id']); if None, abort(404).
        """
        owner_expense_id = _insert_expense("owner@spendly.com", description="Owner expense")
        response = other_client.post(
            f"/expenses/{owner_expense_id}/delete",
            data={"csrf_token": _get_csrf_token(other_client)},
        )
        assert response.status_code == 404, (
            "POSTing to another user's expense id must return 404"
        )

    def test_post_other_users_expense_does_not_delete_row(self, auth_client, other_client):
        """
        The ownership-guarded 404 must leave the expense row intact in the DB.
        """
        owner_expense_id = _insert_expense("owner@spendly.com", description="Should survive")
        other_client.post(
            f"/expenses/{owner_expense_id}/delete",
            data={"csrf_token": _get_csrf_token(other_client)},
        )
        assert _fetch_expense_by_id(owner_expense_id) is not None, (
            "Expense must not be deleted when the requesting user is not the owner"
        )

    def test_post_nonexistent_id_returns_404(self, auth_client):
        """
        POSTing to an id that does not exist at all must return 404.
        No row means get_expense_by_id returns None → abort(404).
        """
        response = auth_client.post(
            "/expenses/99999/delete",
            data={"csrf_token": _get_csrf_token(auth_client)},
        )
        assert response.status_code == 404, (
            "POST to a non-existent expense id must return 404"
        )


# ---------------------------------------------------------------------------
# Happy path — correct deletion behavior
# ---------------------------------------------------------------------------

class TestHappyPath:
    def test_post_own_expense_redirects_to_profile(self, auth_client):
        """
        POSTing to delete an expense the logged-in user owns must return 302
        and redirect to /profile.
        """
        expense_id = _insert_expense("owner@spendly.com")
        response = auth_client.post(
            f"/expenses/{expense_id}/delete",
            data={"csrf_token": _get_csrf_token(auth_client)},
        )
        assert response.status_code == 302, (
            "Successful delete POST must return 302"
        )
        assert "/profile" in response.headers["Location"], (
            "Successful delete must redirect to /profile"
        )

    def test_post_own_expense_removes_row_from_db(self, auth_client):
        """
        After a successful delete POST, the expense row must no longer exist
        in the DB.  This confirms the DELETE query actually ran.
        """
        expense_id = _insert_expense("owner@spendly.com", description="To be deleted")
        assert _fetch_expense_by_id(expense_id) is not None, (
            "Precondition: expense must exist before delete"
        )
        auth_client.post(
            f"/expenses/{expense_id}/delete",
            data={"csrf_token": _get_csrf_token(auth_client)},
        )
        assert _fetch_expense_by_id(expense_id) is None, (
            "Expense row must be absent from DB after successful delete"
        )

    def test_post_own_expense_count_decreases_by_one(self, auth_client):
        """
        Deleting one expense must reduce the user's total expense count by exactly 1.
        """
        id1 = _insert_expense("owner@spendly.com", description="Keep me")
        id2 = _insert_expense("owner@spendly.com", amount=200.0, description="Delete me")
        assert _count_expenses_for_email("owner@spendly.com") == 2, (
            "Precondition: two expenses must exist before delete"
        )
        auth_client.post(
            f"/expenses/{id2}/delete",
            data={"csrf_token": _get_csrf_token(auth_client)},
        )
        assert _count_expenses_for_email("owner@spendly.com") == 1, (
            "Deleting one expense must leave exactly one expense remaining"
        )

    def test_post_deletes_only_targeted_expense(self, auth_client):
        """
        Only the targeted expense row must be removed; other rows for the same
        user must remain intact.
        """
        id_keep = _insert_expense("owner@spendly.com", description="Keep me")
        id_delete = _insert_expense("owner@spendly.com", amount=300.0, description="Delete me")
        auth_client.post(
            f"/expenses/{id_delete}/delete",
            data={"csrf_token": _get_csrf_token(auth_client)},
        )
        assert _fetch_expense_by_id(id_keep) is not None, (
            "The non-targeted expense must still exist after deleting the other one"
        )
        assert _fetch_expense_by_id(id_delete) is None, (
            "The targeted expense must be gone after delete"
        )

    def test_deleted_expense_absent_from_profile_page(self, auth_client):
        """
        After the redirect, the deleted expense's description must no longer
        appear in the profile page's transactions list.
        """
        expense_id = _insert_expense(
            "owner@spendly.com",
            description="UniqueDeletedExpenseXYZ",
        )
        auth_client.post(
            f"/expenses/{expense_id}/delete",
            data={"csrf_token": _get_csrf_token(auth_client)},
        )
        profile_resp = auth_client.get("/profile")
        assert profile_resp.status_code == 200, (
            "/profile must return 200 after deletion"
        )
        html = profile_resp.data.decode()
        assert "UniqueDeletedExpenseXYZ" not in html, (
            "Deleted expense description must not appear in the profile transactions list"
        )

    def test_remaining_expense_still_visible_after_delete(self, auth_client):
        """
        After deleting one expense, another expense for the same user must
        still be visible on the profile page.
        """
        _insert_expense("owner@spendly.com", description="I should remain visible")
        id_delete = _insert_expense(
            "owner@spendly.com", amount=99.0, description="Gone after delete"
        )
        auth_client.post(
            f"/expenses/{id_delete}/delete",
            data={"csrf_token": _get_csrf_token(auth_client)},
        )
        profile_resp = auth_client.get("/profile")
        html = profile_resp.data.decode()
        assert "I should remain visible" in html, (
            "Surviving expense description must still appear on /profile after sibling delete"
        )

    def test_can_delete_all_expenses_one_by_one(self, auth_client):
        """
        Deleting every expense one by one must leave the user with zero rows in the DB.
        """
        id1 = _insert_expense("owner@spendly.com", description="First")
        id2 = _insert_expense("owner@spendly.com", amount=200.0, description="Second")
        token = _get_csrf_token(auth_client)
        auth_client.post(f"/expenses/{id1}/delete", data={"csrf_token": token})
        auth_client.post(f"/expenses/{id2}/delete", data={"csrf_token": token})
        assert _count_expenses_for_email("owner@spendly.com") == 0, (
            "All expenses must be removable; count must be 0 after deleting both"
        )


# ---------------------------------------------------------------------------
# Cross-user isolation — deleting does not affect another user's expenses
# ---------------------------------------------------------------------------

class TestCrossUserIsolation:
    def test_deleting_own_expense_does_not_affect_other_user(
        self, auth_client, other_client
    ):
        """
        When owner deletes their own expense, the other user's expenses must
        be completely unaffected.
        """
        owner_expense_id = _insert_expense("owner@spendly.com", description="Owner deletes this")
        other_expense_id = _insert_expense("other@spendly.com", description="Other keeps this")

        auth_client.post(
            f"/expenses/{owner_expense_id}/delete",
            data={"csrf_token": _get_csrf_token(auth_client)},
        )

        assert _fetch_expense_by_id(other_expense_id) is not None, (
            "Deleting owner's expense must not remove the other user's expense"
        )

    def test_other_user_cannot_delete_owners_expense_leaves_count_unchanged(
        self, auth_client, other_client
    ):
        """
        An ownership-blocked delete attempt must leave the owner's expense
        count unchanged.
        """
        _insert_expense("owner@spendly.com", description="Protected")
        _insert_expense("owner@spendly.com", amount=500.0, description="Also protected")
        assert _count_expenses_for_email("owner@spendly.com") == 2

        # other_client tries (and fails) to delete first owner expense
        owner_expenses = []
        conn = get_db()
        rows = conn.execute(
            "SELECT e.id FROM expenses e "
            "JOIN users u ON u.id = e.user_id "
            "WHERE u.email = ? ORDER BY e.id",
            ("owner@spendly.com",),
        ).fetchall()
        conn.close()
        other_token = _get_csrf_token(other_client)
        for r in rows:
            other_client.post(
                f"/expenses/{r['id']}/delete",
                data={"csrf_token": other_token},
            )

        assert _count_expenses_for_email("owner@spendly.com") == 2, (
            "Owner's expense count must be unchanged after blocked cross-user delete attempts"
        )


# ---------------------------------------------------------------------------
# Profile page — delete button template requirements
# ---------------------------------------------------------------------------

class TestProfileDeleteButton:
    def test_profile_shows_delete_form_for_each_expense(self, auth_client):
        """
        The profile page must contain at least one <form> element that posts to
        the delete URL when the user has expenses.  The spec requires a
        <form method="POST"> per transaction row.
        """
        expense_id = _insert_expense("owner@spendly.com", description="Profile form test")
        html = auth_client.get("/profile").data.decode()
        expected_action = f"/expenses/{expense_id}/delete"
        assert expected_action in html, (
            f"Profile page must contain a form whose action points to "
            f"'/expenses/{expense_id}/delete'"
        )

    def test_profile_delete_form_uses_post_method(self, auth_client):
        """
        The delete form on the profile page must use method='POST' (case-insensitive).
        A GET form would allow link prefetchers to trigger unintended deletions.
        """
        _insert_expense("owner@spendly.com", description="Method check")
        html = auth_client.get("/profile").data.decode().lower()
        # Both method="post" and method="POST" are acceptable
        assert 'method="post"' in html or "method='post'" in html, (
            "Delete form on profile page must declare method='post'"
        )

    def test_profile_delete_form_has_confirm_onsubmit(self, auth_client):
        """
        The spec requires an onsubmit="return confirm('Delete this expense?')"
        attribute on the delete form to provide a client-side guard.
        """
        _insert_expense("owner@spendly.com", description="Confirm guard test")
        html = auth_client.get("/profile").data.decode()
        assert "confirm(" in html, (
            "Delete form must include a confirm() call as a client-side guard "
            "(either inline onsubmit or in a script block)"
        )

    def test_profile_delete_button_present_for_multiple_expenses(self, auth_client):
        """
        Every transaction row must have its own delete form pointing to the
        correct per-row URL.
        """
        id1 = _insert_expense("owner@spendly.com", description="Row one")
        id2 = _insert_expense("owner@spendly.com", amount=200.0, description="Row two")
        html = auth_client.get("/profile").data.decode()
        assert f"/expenses/{id1}/delete" in html, (
            f"Delete form for expense {id1} must appear on the profile page"
        )
        assert f"/expenses/{id2}/delete" in html, (
            f"Delete form for expense {id2} must appear on the profile page"
        )

    def test_profile_currency_is_rupee_not_dollar(self, auth_client):
        """
        The spec mandates ₹ (Indian Rupees) throughout.  After adding an expense
        the profile page must not contain a '$' sign anywhere.
        """
        _insert_expense("owner@spendly.com", amount=750.0, description="Rupee check")
        html = auth_client.get("/profile").data.decode()
        assert "$" not in html, (
            "Profile page must not contain '$' — currency must be ₹"
        )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_double_delete_second_attempt_returns_404(self, auth_client):
        """
        Attempting to delete the same expense twice: the first call succeeds
        and the second must return 404 (row no longer exists → get_expense_by_id
        returns None → abort(404)).
        """
        expense_id = _insert_expense("owner@spendly.com", description="Delete twice")
        token = _get_csrf_token(auth_client)
        first = auth_client.post(f"/expenses/{expense_id}/delete", data={"csrf_token": token})
        assert first.status_code == 302, "First delete must succeed with 302"
        second = auth_client.post(f"/expenses/{expense_id}/delete", data={"csrf_token": token})
        assert second.status_code == 404, (
            "Second delete of the same (now-gone) expense must return 404"
        )

    def test_post_to_zero_id_returns_404(self, auth_client):
        """
        id=0 can never be a valid AUTOINCREMENT primary key; the route should
        return 404 (no such expense found for the current user).
        Note: Flask may return 404 for non-matching int converter too; either
        404 or 405 is acceptable, but never 200 or 302.
        """
        response = auth_client.post(
            "/expenses/0/delete",
            data={"csrf_token": _get_csrf_token(auth_client)},
        )
        assert response.status_code in (404, 405), (
            "POST /expenses/0/delete must not succeed — expected 404 or 405"
        )

    @pytest.mark.parametrize("expense_id", [9999991, 9999992, 9999993])
    def test_post_to_large_nonexistent_ids_returns_404(self, auth_client, expense_id):
        """
        Large integer ids that do not correspond to any row must return 404.
        """
        response = auth_client.post(
            f"/expenses/{expense_id}/delete",
            data={"csrf_token": _get_csrf_token(auth_client)},
        )
        assert response.status_code == 404, (
            f"POST /expenses/{expense_id}/delete for a non-existent id must return 404"
        )
