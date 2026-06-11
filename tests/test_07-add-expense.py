"""
tests/test_07-add-expense.py

Tests for the Step 07 "Add Expense" feature.

All test logic is derived exclusively from the feature spec
(.claude/specs/07-add-expense.md).  The implementation is NOT read for
test logic.

Routes under test:
  GET  /expenses/add  — render the add-expense form (auth required)
  POST /expenses/add  — validate and insert expense, redirect to /profile (auth required)

Fixture strategy:
  - Uses shared `app`, `client` fixtures from conftest.py (tmp-path-isolated SQLite DB).
  - Defines a local `auth_client` fixture that registers + logs in a fresh user.
  - Defines a local helper `_db_expenses` to query the DB directly for side-effect checks.
"""

from datetime import date

import pytest
from werkzeug.security import generate_password_hash

from database.db import get_db

# ---------------------------------------------------------------------------
# Local fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_client(app, client):
    """
    A test client that already has a logged-in session.
    Inserts a user directly into the DB (avoids coupling to the register route)
    then authenticates via POST /login.
    """
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "test@spendly.com", generate_password_hash("testpass1")),
    )
    conn.commit()
    conn.close()

    resp = client.post(
        "/login",
        data={"email": "test@spendly.com", "password": "testpass1"},
        follow_redirects=False,
    )
    assert resp.status_code == 302, "Login should redirect on success"
    return client


def _db_expenses(user_email):
    """
    Return all expense rows for the user identified by email.
    Queries the live (tmp-path) DB directly — used to verify DB side effects.
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT e.id, e.amount, e.category, e.date, e.description "
        "FROM expenses e "
        "JOIN users u ON u.id = e.user_id "
        "WHERE u.email = ? "
        "ORDER BY e.id",
        (user_email,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

class TestAuthGuard:
    def test_get_add_expense_unauthenticated_redirects(self, client):
        response = client.get("/expenses/add")
        assert response.status_code == 302, (
            "GET /expenses/add without login should return 302"
        )
        assert "/login" in response.headers["Location"], (
            "Unauthenticated GET /expenses/add should redirect to /login"
        )

    def test_post_add_expense_unauthenticated_redirects(self, client):
        response = client.post("/expenses/add", data={
            "amount": "100",
            "category": "Food",
            "date": "2026-06-01",
            "description": "Test",
        })
        assert response.status_code == 302, (
            "POST /expenses/add without login should return 302"
        )
        assert "/login" in response.headers["Location"], (
            "Unauthenticated POST /expenses/add should redirect to /login"
        )


# ---------------------------------------------------------------------------
# GET — form rendering
# ---------------------------------------------------------------------------

class TestGetForm:
    def test_get_returns_200(self, auth_client):
        response = auth_client.get("/expenses/add")
        assert response.status_code == 200, (
            "GET /expenses/add while logged in should return 200"
        )

    def test_get_contains_amount_field(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert 'name="amount"' in html, (
            "Form must contain an input with name='amount'"
        )

    def test_get_contains_category_field(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert 'name="category"' in html, (
            "Form must contain a field with name='category'"
        )

    def test_get_contains_date_field(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert 'name="date"' in html, (
            "Form must contain an input with name='date'"
        )

    def test_get_contains_description_field(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert 'name="description"' in html, (
            "Form must contain a field with name='description'"
        )

    def test_get_date_field_defaults_to_today(self, auth_client):
        """The date field value attribute must equal today's ISO date (YYYY-MM-DD)."""
        today = date.today().isoformat()
        html = auth_client.get("/expenses/add").data.decode()
        assert today in html, (
            f"Date field should default to today's date ({today}) on first GET"
        )

    def test_get_category_select_contains_food(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert "Food" in html, "Category select must include 'Food'"

    def test_get_category_select_contains_travel(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert "Travel" in html, "Category select must include 'Travel'"

    def test_get_category_select_contains_bills(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert "Bills" in html, "Category select must include 'Bills'"

    def test_get_category_select_contains_entertainment(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert "Entertainment" in html, "Category select must include 'Entertainment'"

    def test_get_category_select_contains_health(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert "Health" in html, "Category select must include 'Health'"

    def test_get_category_select_contains_other(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert "Other" in html, "Category select must include 'Other'"

    def test_get_category_is_select_element(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert "<select" in html, (
            "Category must be rendered as a <select> element"
        )

    def test_get_no_dollar_sign(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert "$" not in html, (
            "Form page must not contain $ — currency should be ₹"
        )

    def test_get_no_pound_sign(self, auth_client):
        html = auth_client.get("/expenses/add").data.decode()
        assert "£" not in html, (
            "Form page must not contain £ — currency should be ₹"
        )


# ---------------------------------------------------------------------------
# POST — happy path
# ---------------------------------------------------------------------------

class TestPostHappyPath:
    def test_valid_post_redirects_to_profile(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "amount": "250",
            "category": "Food",
            "date": "2026-06-01",
            "description": "Lunch",
        })
        assert response.status_code == 302, (
            "Valid POST /expenses/add should return 302 redirect"
        )
        assert "/profile" in response.headers["Location"], (
            "Valid POST should redirect to /profile"
        )

    def test_valid_post_inserts_row_in_db(self, app, auth_client):
        auth_client.post("/expenses/add", data={
            "amount": "499.50",
            "category": "Travel",
            "date": "2026-06-05",
            "description": "Train ticket",
        })
        rows = _db_expenses("test@spendly.com")
        assert len(rows) == 1, "Exactly one expense row should exist after a valid POST"
        row = rows[0]
        assert row["amount"] == 499.50, "Stored amount must match submitted value"
        assert row["category"] == "Travel", "Stored category must match submitted value"
        assert row["date"] == "2026-06-05", "Stored date must match submitted value"
        assert row["description"] == "Train ticket", "Stored description must match submitted value"

    def test_valid_post_without_description_succeeds(self, app, auth_client):
        """Description is optional — omitting it must still insert the row."""
        response = auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": "Other",
            "date": "2026-06-10",
        })
        assert response.status_code == 302, (
            "POST without description should still redirect (description is optional)"
        )
        rows = _db_expenses("test@spendly.com")
        assert len(rows) == 1, "Expense row must exist even when description is omitted"

    def test_valid_post_description_empty_string_succeeds(self, app, auth_client):
        """Explicitly submitting an empty description string must also succeed."""
        response = auth_client.post("/expenses/add", data={
            "amount": "75",
            "category": "Health",
            "date": "2026-06-12",
            "description": "",
        })
        assert response.status_code == 302, (
            "POST with empty description string should redirect"
        )

    def test_valid_post_with_decimal_amount(self, app, auth_client):
        """Decimal amounts (e.g. 1234.56) must be accepted and stored correctly."""
        auth_client.post("/expenses/add", data={
            "amount": "1234.56",
            "category": "Bills",
            "date": "2026-06-03",
            "description": "Internet bill",
        })
        rows = _db_expenses("test@spendly.com")
        assert len(rows) == 1
        assert abs(rows[0]["amount"] - 1234.56) < 0.001, (
            "Decimal amount should be stored accurately"
        )

    def test_valid_post_new_expense_appears_on_profile(self, auth_client):
        """After the redirect, the expense description should be visible on /profile."""
        auth_client.post("/expenses/add", data={
            "amount": "300",
            "category": "Entertainment",
            "date": "2026-06-08",
            "description": "Concert tickets",
        })
        profile_resp = auth_client.get("/profile")
        assert profile_resp.status_code == 200
        html = profile_resp.data.decode()
        assert "Concert tickets" in html, (
            "Newly added expense description should appear in the transactions list on /profile"
        )

    def test_valid_post_amount_appears_on_profile(self, auth_client):
        """The amount of the new expense should appear on /profile after redirect."""
        auth_client.post("/expenses/add", data={
            "amount": "999",
            "category": "Entertainment",
            "date": "2026-06-09",
            "description": "New shoes",
        })
        profile_resp = auth_client.get("/profile")
        html = profile_resp.data.decode()
        assert "₹999" in html, (
            "Newly added expense amount should appear as ₹999 on /profile"
        )

    @pytest.mark.parametrize("category", ["Food", "Travel", "Bills", "Entertainment", "Health", "Other", "Shopping"])
    def test_valid_post_all_allowed_categories(self, app, auth_client, category):
        """Every allowed category must be accepted without error."""
        response = auth_client.post("/expenses/add", data={
            "amount": "50",
            "category": category,
            "date": "2026-06-01",
            "description": f"Test {category}",
        })
        assert response.status_code == 302, (
            f"POST with category='{category}' should redirect (valid category)"
        )


# ---------------------------------------------------------------------------
# POST — validation: amount
# ---------------------------------------------------------------------------

class TestPostAmountValidation:
    def test_missing_amount_returns_200_with_error(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "category": "Food",
            "date": "2026-06-01",
            "description": "Lunch",
        })
        assert response.status_code == 200, (
            "POST with missing amount should re-render the form (200)"
        )
        html = response.data.decode()
        assert "error" in html.lower() or "amount" in html.lower(), (
            "Response should contain an error message about the amount"
        )

    def test_empty_amount_returns_200_with_error(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "amount": "",
            "category": "Food",
            "date": "2026-06-01",
            "description": "Lunch",
        })
        assert response.status_code == 200, (
            "POST with empty amount should re-render the form (200)"
        )

    def test_zero_amount_returns_200_with_error(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "amount": "0",
            "category": "Food",
            "date": "2026-06-01",
            "description": "Free item",
        })
        assert response.status_code == 200, (
            "POST with amount=0 should re-render the form (200)"
        )
        html = response.data.decode()
        assert "positive" in html.lower() or "error" in html.lower(), (
            "Response should indicate that amount must be positive"
        )

    def test_negative_amount_returns_200_with_error(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "amount": "-50",
            "category": "Food",
            "date": "2026-06-01",
            "description": "Refund",
        })
        assert response.status_code == 200, (
            "POST with negative amount should re-render the form (200)"
        )
        html = response.data.decode()
        assert "positive" in html.lower() or "error" in html.lower(), (
            "Response should indicate that amount must be positive"
        )

    def test_non_numeric_amount_returns_200_with_error(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-06-01",
            "description": "Lunch",
        })
        assert response.status_code == 200, (
            "POST with non-numeric amount should re-render the form (200)"
        )

    def test_invalid_amount_does_not_insert_row(self, app, auth_client):
        auth_client.post("/expenses/add", data={
            "amount": "0",
            "category": "Food",
            "date": "2026-06-01",
        })
        rows = _db_expenses("test@spendly.com")
        assert len(rows) == 0, (
            "A validation failure on amount must not insert any expense row"
        )

    @pytest.mark.parametrize("bad_amount", ["0", "-1", "-0.01", "abc", "", "0.0", "not-a-number"])
    def test_parametrized_bad_amounts_all_return_200(self, auth_client, bad_amount):
        response = auth_client.post("/expenses/add", data={
            "amount": bad_amount,
            "category": "Food",
            "date": "2026-06-01",
            "description": "Test",
        })
        assert response.status_code == 200, (
            f"POST with amount='{bad_amount}' should re-render the form (200), not redirect"
        )


# ---------------------------------------------------------------------------
# POST — validation: category
# ---------------------------------------------------------------------------

class TestPostCategoryValidation:
    def test_missing_category_returns_200_with_error(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "amount": "100",
            "date": "2026-06-01",
            "description": "Lunch",
        })
        assert response.status_code == 200, (
            "POST with missing category should re-render the form (200)"
        )

    def test_empty_category_returns_200_with_error(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": "",
            "date": "2026-06-01",
            "description": "Lunch",
        })
        assert response.status_code == 200, (
            "POST with empty category should re-render the form (200)"
        )
        html = response.data.decode()
        assert "category" in html.lower() or "error" in html.lower(), (
            "Response should contain an error about the category"
        )

    def test_invalid_category_value_returns_200_with_error(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": "InvalidCat",
            "date": "2026-06-01",
            "description": "Lunch",
        })
        assert response.status_code == 200, (
            "POST with invalid category should re-render the form (200)"
        )
        html = response.data.decode()
        assert "category" in html.lower() or "error" in html.lower(), (
            "Response should indicate the category is invalid"
        )

    def test_invalid_category_does_not_insert_row(self, app, auth_client):
        auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": "NonExistent",
            "date": "2026-06-01",
        })
        rows = _db_expenses("test@spendly.com")
        assert len(rows) == 0, (
            "An invalid category must not insert any expense row into the DB"
        )

    @pytest.mark.parametrize("bad_category", [
        "food",          # wrong case
        "FOOD",          # all-caps
        # "Shopping" is now a valid category — removed from bad list
        "Transport",     # not in the allowed list
        "Groceries",     # arbitrary invalid value
        " Food",         # leading space
        "Food ",         # trailing space
    ])
    def test_parametrized_bad_categories_all_return_200(self, auth_client, bad_category):
        response = auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": bad_category,
            "date": "2026-06-01",
            "description": "Test",
        })
        assert response.status_code == 200, (
            f"POST with category='{bad_category}' should re-render (200), not redirect"
        )


# ---------------------------------------------------------------------------
# POST — validation: date
# ---------------------------------------------------------------------------

class TestPostDateValidation:
    def test_missing_date_returns_200_with_error(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": "Food",
            "description": "Lunch",
        })
        assert response.status_code == 200, (
            "POST with missing date should re-render the form (200)"
        )

    def test_empty_date_returns_200_with_error(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": "Food",
            "date": "",
            "description": "Lunch",
        })
        assert response.status_code == 200, (
            "POST with empty date should re-render the form (200)"
        )
        html = response.data.decode()
        assert "date" in html.lower() or "error" in html.lower(), (
            "Response should contain an error about the date"
        )

    def test_invalid_date_string_returns_200_with_error(self, auth_client):
        response = auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": "Food",
            "date": "not-a-date",
            "description": "Lunch",
        })
        assert response.status_code == 200, (
            "POST with date='not-a-date' should re-render the form (200)"
        )

    def test_invalid_date_does_not_insert_row(self, app, auth_client):
        auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": "Food",
            "date": "bad-date",
        })
        rows = _db_expenses("test@spendly.com")
        assert len(rows) == 0, (
            "An invalid date must not insert any expense row into the DB"
        )

    @pytest.mark.parametrize("bad_date", [
        "not-a-date",
        "01/06/2026",     # DD/MM/YYYY — not ISO format
        "June 1 2026",    # natural language
        "2026-13-01",     # month 13 — invalid
        "2026-06-32",     # day 32 — invalid
        "20260601",       # missing hyphens
        "",
    ])
    def test_parametrized_bad_dates_all_return_200(self, auth_client, bad_date):
        response = auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": "Food",
            "date": bad_date,
            "description": "Test",
        })
        assert response.status_code == 200, (
            f"POST with date='{bad_date}' should re-render (200), not redirect"
        )


# ---------------------------------------------------------------------------
# POST — field preservation on validation failure
# ---------------------------------------------------------------------------

class TestFieldPreservationOnError:
    def test_amount_preserved_when_category_invalid(self, auth_client):
        """When category fails, the submitted amount should be pre-filled in the re-render."""
        html = auth_client.post("/expenses/add", data={
            "amount": "777",
            "category": "BadCat",
            "date": "2026-06-01",
            "description": "Testing preservation",
        }).data.decode()
        assert "777" in html, (
            "Amount '777' should be pre-filled in the re-rendered form after category error"
        )

    def test_description_preserved_when_amount_invalid(self, auth_client):
        """When amount fails, the submitted description should be pre-filled."""
        html = auth_client.post("/expenses/add", data={
            "amount": "-10",
            "category": "Food",
            "date": "2026-06-01",
            "description": "My unique description text",
        }).data.decode()
        assert "My unique description text" in html, (
            "Description should be pre-filled in the re-rendered form after amount error"
        )

    def test_date_preserved_when_category_invalid(self, auth_client):
        """When category fails, the submitted date should be pre-filled."""
        html = auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": "BadCat",
            "date": "2026-07-15",
            "description": "Some text",
        }).data.decode()
        assert "2026-07-15" in html, (
            "Date '2026-07-15' should be pre-filled in the re-rendered form after category error"
        )

    def test_category_options_still_present_on_error(self, auth_client):
        """After a validation error the category <select> must still render all options."""
        html = auth_client.post("/expenses/add", data={
            "amount": "-5",
            "category": "Food",
            "date": "2026-06-01",
        }).data.decode()
        for cat in ["Food", "Travel", "Bills", "Entertainment", "Health", "Other", "Shopping"]:
            assert cat in html, (
                f"Category option '{cat}' should still appear in the re-rendered form"
            )


# ---------------------------------------------------------------------------
# DB isolation — multiple independent expenses for same user
# ---------------------------------------------------------------------------

class TestDbIsolation:
    def test_two_valid_posts_insert_two_rows(self, app, auth_client):
        auth_client.post("/expenses/add", data={
            "amount": "100",
            "category": "Food",
            "date": "2026-06-01",
            "description": "First expense",
        })
        auth_client.post("/expenses/add", data={
            "amount": "200",
            "category": "Bills",
            "date": "2026-06-02",
            "description": "Second expense",
        })
        rows = _db_expenses("test@spendly.com")
        assert len(rows) == 2, "Two valid POSTs should result in exactly two expense rows"

    def test_failed_post_between_valid_posts_does_not_affect_count(self, app, auth_client):
        auth_client.post("/expenses/add", data={
            "amount": "50",
            "category": "Other",
            "date": "2026-06-01",
            "description": "Before failure",
        })
        # This one should fail — bad category
        auth_client.post("/expenses/add", data={
            "amount": "99",
            "category": "Invalid",
            "date": "2026-06-02",
        })
        auth_client.post("/expenses/add", data={
            "amount": "75",
            "category": "Health",
            "date": "2026-06-03",
            "description": "After failure",
        })
        rows = _db_expenses("test@spendly.com")
        assert len(rows) == 2, (
            "Only the two valid POSTs should have inserted rows; "
            "the failed POST in the middle must not affect the count"
        )

    def test_expenses_belong_to_correct_user(self, app, auth_client):
        """An expense inserted via auth_client must not appear under a different user."""
        # Insert a second independent user
        conn = get_db()
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Other User", "other@spendly.com", generate_password_hash("otherpass1")),
        )
        conn.commit()
        conn.close()

        auth_client.post("/expenses/add", data={
            "amount": "123",
            "category": "Travel",
            "date": "2026-06-05",
            "description": "My trip",
        })

        own_rows = _db_expenses("test@spendly.com")
        other_rows = _db_expenses("other@spendly.com")

        assert len(own_rows) == 1, "Logged-in user should have exactly one expense"
        assert len(other_rows) == 0, "Other user should have no expenses"
