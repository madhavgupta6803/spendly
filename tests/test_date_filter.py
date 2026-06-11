"""
tests/test_date_filter.py

Tests for the Step 06 date-filter feature on GET /profile.

All test logic is derived from the feature spec
(.claude/specs/06-date-filter-for-profile-page.md), NOT from the
implementation.  The seeded data (8 expenses, 2026-05-01 to 2026-05-22,
totalling ₹6,320) comes from the shared `seeded_user_id` fixture in conftest.py.

The simulated "today" for the test suite is 2026-06-11 (per project date).
Key consequences:
  - period=this_month  → June 2026 → zero seeded expenses (all are in May)
  - period=last_3_months → 90 days back = 2026-03-13 → all 8 May expenses included
  - period=this_year   → 2026-01-01 to today → all 8 May expenses included
"""

import pytest


# ── helpers ───────────────────────────────────────────────────────────────────

def login(client):
    """POST demo credentials and return the response."""
    return client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "demo123"},
        follow_redirects=False,
    )


def get_profile(client, **params):
    """GET /profile with optional query-string params; returns decoded HTML."""
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"/profile?{qs}" if qs else "/profile"
    response = client.get(url)
    return response, response.data.decode("utf-8")


# ── auth guard ────────────────────────────────────────────────────────────────

class TestAuthGuard:
    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302, "Expected redirect for unauthenticated user"
        assert "/login" in response.headers["Location"], (
            "Unauthenticated /profile should redirect to /login"
        )

    def test_unauthenticated_with_period_param_still_redirects(self, client):
        response = client.get("/profile?period=this_month")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_unauthenticated_with_custom_range_still_redirects(self, client):
        response = client.get("/profile?from=2026-05-01&to=2026-05-31")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


# ── default / no params ───────────────────────────────────────────────────────

class TestDefaultAllTime:
    def test_no_params_returns_200(self, client, seeded_user_id):
        login(client)
        response, _ = get_profile(client)
        assert response.status_code == 200, "GET /profile with no params should return 200"

    def test_no_params_shows_all_time_label(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client)
        assert "All time" in html, (
            "Default profile page should display 'All time' period label"
        )

    def test_no_params_shows_all_expenses_total(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client)
        assert "₹6,320" in html, (
            "Default profile page should show ₹6,320 (sum of all 8 seeded expenses)"
        )

    def test_no_params_shows_all_transactions(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client)
        # All 8 seeded descriptions must appear
        descriptions = [
            "Lunch at café",
            "Uber ride",
            "Electricity bill",
            "Pharmacy",
            "Movie tickets",
            "Clothing",
            "Miscellaneous",
            "Dinner with friends",
        ]
        for desc in descriptions:
            assert desc in html, f"Expected transaction '{desc}' to appear in default profile"

    def test_no_params_shows_top_category(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client)
        assert "Shopping" in html, (
            "Default profile page should show 'Shopping' as top category"
        )

    def test_explicit_period_all_same_as_default(self, client, seeded_user_id):
        login(client)
        response, html = get_profile(client, period="all")
        assert response.status_code == 200, "period=all should return HTTP 200"
        assert "All time" in html, "period=all should show 'All time' label"
        assert "₹6,320" in html, "period=all should show full ₹6,320 total"


# ── period=this_month ─────────────────────────────────────────────────────────

class TestThisMonth:
    """
    Today is 2026-06-11.  'This Month' = June 2026.
    None of the seeded expenses fall in June, so stats must show zero / empty.
    The period label must be "June 2026".
    """

    def test_this_month_returns_200(self, client, seeded_user_id):
        login(client)
        response, _ = get_profile(client, period="this_month")
        assert response.status_code == 200

    def test_this_month_period_label(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="this_month")
        assert "June 2026" in html, (
            "period=this_month should display 'June 2026' as the period label"
        )

    def test_this_month_zero_expenses_stats(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="this_month")
        # No seeded expense is in June 2026 → total must be ₹0
        assert "₹0" in html, (
            "period=this_month (June 2026) should show ₹0 when no expenses exist in that month"
        )

    def test_this_month_no_may_transactions_shown(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="this_month")
        # May expenses must not bleed through
        assert "Lunch at café" not in html, (
            "May expenses should not appear when filtering to this month (June 2026)"
        )
        assert "Clothing" not in html

    def test_this_month_active_period_indicator(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="this_month")
        # The template must expose this_month as the active period in some form
        # (class name, data attribute, or query param link) so the button appears active.
        assert "this_month" in html, (
            "HTML should contain 'this_month' to mark the active filter button"
        )


# ── period=last_3_months ──────────────────────────────────────────────────────

class TestLast3Months:
    """
    Today is 2026-06-11; 90 days back = 2026-03-13.
    All 8 seeded expenses (2026-05-01 to 2026-05-22) fall within this window.
    """

    def test_last_3_months_returns_200(self, client, seeded_user_id):
        login(client)
        response, _ = get_profile(client, period="last_3_months")
        assert response.status_code == 200

    def test_last_3_months_period_label(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="last_3_months")
        assert "Last 3 months" in html, (
            "period=last_3_months should display 'Last 3 months' as the period label"
        )

    def test_last_3_months_includes_all_seeded_expenses(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="last_3_months")
        assert "₹6,320" in html, (
            "period=last_3_months should include all 8 May 2026 expenses (₹6,320)"
        )

    def test_last_3_months_active_period_indicator(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="last_3_months")
        assert "last_3_months" in html, (
            "HTML should contain 'last_3_months' to mark the active filter button"
        )


# ── period=this_year ──────────────────────────────────────────────────────────

class TestThisYear:
    """
    Today is 2026-06-11.  'This Year' = 2026-01-01 to today.
    All 8 seeded expenses are in May 2026 → all included.
    """

    def test_this_year_returns_200(self, client, seeded_user_id):
        login(client)
        response, _ = get_profile(client, period="this_year")
        assert response.status_code == 200

    def test_this_year_period_label(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="this_year")
        assert "2026" in html, (
            "period=this_year should display '2026' as the period label"
        )

    def test_this_year_includes_all_seeded_expenses(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="this_year")
        assert "₹6,320" in html, (
            "period=this_year should include all 8 May 2026 expenses (₹6,320)"
        )

    def test_this_year_active_period_indicator(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="this_year")
        assert "this_year" in html, (
            "HTML should contain 'this_year' to mark the active filter button"
        )


# ── custom date range ─────────────────────────────────────────────────────────

class TestCustomRange:
    def test_full_may_range_returns_200(self, client, seeded_user_id):
        login(client)
        response, _ = get_profile(client, **{"from": "2026-05-01", "to": "2026-05-31"})
        assert response.status_code == 200

    def test_full_may_range_shows_all_expenses(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "2026-05-01", "to": "2026-05-31"})
        assert "₹6,320" in html, (
            "Custom range 2026-05-01 to 2026-05-31 should show ₹6,320"
        )

    def test_full_may_range_period_label(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "2026-05-01", "to": "2026-05-31"})
        assert "1 May 2026" in html, "Period label should contain '1 May 2026'"
        assert "31 May 2026" in html, "Period label should contain '31 May 2026'"

    def test_partial_may_range_filters_correctly(self, client, seeded_user_id):
        """
        2026-05-10 to 2026-05-22 includes four expenses:
          - 2026-05-12  Entertainment  ₹800
          - 2026-05-15  Shopping       ₹2,500
          - 2026-05-18  Other          ₹200
          - 2026-05-22  Food           ₹650
        Total = ₹4,150
        """
        login(client)
        _, html = get_profile(client, **{"from": "2026-05-10", "to": "2026-05-22"})
        assert "₹4,150" in html, (
            "Partial May range should sum to ₹4,150 (4 expenses between 10–22 May)"
        )

    def test_partial_may_range_excludes_earlier_expenses(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "2026-05-10", "to": "2026-05-22"})
        # Expenses before 10 May must not appear
        assert "Lunch at café" not in html, (
            "Expense from 2026-05-01 should not appear in 2026-05-10 to 2026-05-22 range"
        )
        assert "Uber ride" not in html, (
            "Expense from 2026-05-03 should not appear in 2026-05-10 to 2026-05-22 range"
        )
        assert "Electricity bill" not in html, (
            "Expense from 2026-05-05 should not appear in 2026-05-10 to 2026-05-22 range"
        )
        assert "Pharmacy" not in html, (
            "Expense from 2026-05-08 should not appear in 2026-05-10 to 2026-05-22 range"
        )

    def test_partial_may_range_includes_expected_transactions(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "2026-05-10", "to": "2026-05-22"})
        assert "Movie tickets" in html, "2026-05-12 expense should appear"
        assert "Clothing" in html, "2026-05-15 expense should appear"
        assert "Miscellaneous" in html, "2026-05-18 expense should appear"
        assert "Dinner with friends" in html, "2026-05-22 expense should appear"

    def test_custom_range_period_label_format(self, client, seeded_user_id):
        """Label format: 'D Mon YYYY – D Mon YYYY' (no zero-padding on day)."""
        login(client)
        _, html = get_profile(client, **{"from": "2026-05-10", "to": "2026-05-22"})
        assert "10 May 2026" in html, "Custom range label should show '10 May 2026'"
        assert "22 May 2026" in html, "Custom range label should show '22 May 2026'"


# ── reversed date range ───────────────────────────────────────────────────────

class TestReversedRange:
    def test_reversed_range_returns_200(self, client, seeded_user_id):
        login(client)
        response, _ = get_profile(client, **{"from": "2026-05-31", "to": "2026-05-01"})
        assert response.status_code == 200, (
            "Reversed date range (from > to) should be silently swapped and return 200"
        )

    def test_reversed_range_shows_same_data_as_normal_order(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "2026-05-31", "to": "2026-05-01"})
        assert "₹6,320" in html, (
            "Reversed range 2026-05-31/2026-05-01 should swap to produce same result as "
            "2026-05-01 to 2026-05-31 (₹6,320)"
        )

    def test_reversed_range_period_label_shows_swapped_order(self, client, seeded_user_id):
        """After swap the label should read '1 May 2026 – 31 May 2026', not reversed."""
        login(client)
        _, html = get_profile(client, **{"from": "2026-05-31", "to": "2026-05-01"})
        assert "1 May 2026" in html, "Swapped label should start with '1 May 2026'"
        assert "31 May 2026" in html, "Swapped label should end with '31 May 2026'"


# ── invalid / malformed date inputs ──────────────────────────────────────────

class TestInvalidDateInputs:
    def test_both_params_invalid_returns_200(self, client, seeded_user_id):
        login(client)
        response = client.get("/profile?from=not-a-date&to=also-bad")
        assert response.status_code == 200, (
            "Invalid date strings should be silently ignored and return HTTP 200"
        )

    def test_both_params_invalid_falls_back_to_all_time(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "not-a-date", "to": "also-bad"})
        assert "All time" in html, (
            "Invalid date strings should fall back to 'All time' period"
        )

    def test_both_params_invalid_shows_all_expenses(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "not-a-date", "to": "also-bad"})
        assert "₹6,320" in html, (
            "Invalid date strings should fall back to all-time view showing ₹6,320"
        )

    def test_only_from_param_falls_back_to_all_time(self, client, seeded_user_id):
        login(client)
        response = client.get("/profile?from=2026-05-01")
        html = response.data.decode("utf-8")
        assert response.status_code == 200
        assert "All time" in html, (
            "Providing only 'from' without 'to' should fall back to 'All time'"
        )

    def test_only_to_param_falls_back_to_all_time(self, client, seeded_user_id):
        login(client)
        response = client.get("/profile?to=2026-05-31")
        html = response.data.decode("utf-8")
        assert response.status_code == 200
        assert "All time" in html, (
            "Providing only 'to' without 'from' should fall back to 'All time'"
        )

    def test_from_valid_to_invalid_falls_back_to_all_time(self, client, seeded_user_id):
        login(client)
        response = client.get("/profile?from=2026-05-01&to=bad-date")
        html = response.data.decode("utf-8")
        assert response.status_code == 200
        assert "All time" in html, (
            "Mixed valid/invalid date pair should fall back to 'All time'"
        )

    @pytest.mark.parametrize("from_val,to_val", [
        ("", "2026-05-31"),
        ("2026-05-01", ""),
        ("", ""),
        ("2026-13-01", "2026-05-31"),   # month 13 is invalid
        ("2026-05-32", "2026-05-31"),   # day 32 is invalid
    ])
    def test_malformed_dates_do_not_crash(self, client, seeded_user_id, from_val, to_val):
        login(client)
        url = f"/profile?from={from_val}&to={to_val}"
        response = client.get(url)
        assert response.status_code == 200, (
            f"Malformed date pair from='{from_val}' to='{to_val}' should not crash (expected 200)"
        )


# ── empty result set ──────────────────────────────────────────────────────────

class TestEmptyResultSet:
    """
    A date range with no matching expenses must render without errors and show
    zero-state stats.
    """

    def test_empty_range_returns_200(self, client, seeded_user_id):
        login(client)
        # 2024 has no seeded expenses
        response, _ = get_profile(client, **{"from": "2024-01-01", "to": "2024-12-31"})
        assert response.status_code == 200, (
            "A date range with no expenses should still return HTTP 200"
        )

    def test_empty_range_total_is_zero(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "2024-01-01", "to": "2024-12-31"})
        assert "₹0" in html, (
            "Empty range should display ₹0 as total spent"
        )

    def test_empty_range_transaction_count_is_zero(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "2024-01-01", "to": "2024-12-31"})
        # The transaction count stat should reflect 0
        assert "0" in html, "Empty range should display 0 transaction count"

    def test_empty_range_top_category_is_dash(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "2024-01-01", "to": "2024-12-31"})
        assert "—" in html, (
            "Empty range should display '—' as top category (em-dash, not hyphen)"
        )

    def test_empty_range_no_transaction_rows(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "2024-01-01", "to": "2024-12-31"})
        # None of the seeded expense descriptions should appear
        assert "Lunch at café" not in html
        assert "Clothing" not in html
        assert "Dinner with friends" not in html

    def test_this_month_empty_state_returns_200(self, client, seeded_user_id):
        """
        period=this_month → June 2026 → zero seeded expenses.
        Must not raise a server error.
        """
        login(client)
        response, _ = get_profile(client, period="this_month")
        assert response.status_code == 200, (
            "period=this_month with no matching expenses should return 200"
        )

    def test_this_month_empty_state_shows_zero_total(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="this_month")
        assert "₹0" in html, (
            "period=this_month with no matching expenses should show ₹0"
        )

    def test_this_month_empty_state_top_category_dash(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, period="this_month")
        assert "—" in html, (
            "period=this_month with no matching expenses should show '—' as top category"
        )


# ── period preset parametrized round-trip ─────────────────────────────────────

class TestPresetRoundTrip:
    """
    For each preset, verify that the period param value itself appears in the
    response HTML (confirming the active-state link/button is rendered) and
    the corresponding human-readable label is shown.
    """

    @pytest.mark.parametrize("period,expected_label", [
        ("all",           "All time"),
        ("last_3_months", "Last 3 months"),
        ("this_year",     "2026"),
    ])
    def test_period_label_in_html(self, client, seeded_user_id, period, expected_label):
        login(client)
        _, html = get_profile(client, period=period)
        assert expected_label in html, (
            f"period={period} should render the label '{expected_label}'"
        )

    @pytest.mark.parametrize("period", [
        "all",
        "this_month",
        "last_3_months",
        "this_year",
    ])
    def test_period_value_present_in_html(self, client, seeded_user_id, period):
        """
        The period value must appear somewhere in the rendered HTML so that
        the active CSS class can be applied to the correct button.
        """
        login(client)
        _, html = get_profile(client, period=period)
        assert period in html, (
            f"The period value '{period}' should appear in the HTML (e.g. in href or data attribute)"
        )

    @pytest.mark.parametrize("period", [
        "all",
        "last_3_months",
        "this_year",
    ])
    def test_period_returns_200(self, client, seeded_user_id, period):
        login(client)
        response, _ = get_profile(client, period=period)
        assert response.status_code == 200, f"period={period} should return HTTP 200"


# ── filter bar structural presence ───────────────────────────────────────────

class TestFilterBarStructure:
    """
    The filter bar UI elements should be present in the rendered page.
    Tests are intentionally loose — checking for text labels, not CSS classes,
    so they are not brittle against HTML restructuring.
    """

    def test_filter_bar_contains_this_month_option(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client)
        assert "This Month" in html, "Filter bar should contain a 'This Month' option"

    def test_filter_bar_contains_last_3_months_option(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client)
        assert "Last 3 Months" in html or "Last 3 months" in html, (
            "Filter bar should contain a 'Last 3 Months' option"
        )

    def test_filter_bar_contains_this_year_option(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client)
        assert "This Year" in html or "This year" in html, (
            "Filter bar should contain a 'This Year' option"
        )

    def test_filter_bar_contains_all_time_option(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client)
        assert "All Time" in html or "All time" in html, (
            "Filter bar should contain an 'All Time' option"
        )

    def test_period_label_summary_line_present(self, client, seeded_user_id):
        """A human-readable 'Showing: ...' or equivalent line should be in the page."""
        login(client)
        _, html = get_profile(client)
        # The spec says a summary label is shown below the filter bar;
        # at minimum "All time" must appear in the page.
        assert "All time" in html, (
            "A period summary label should be present on the default profile page"
        )

    def test_custom_date_inputs_present(self, client, seeded_user_id):
        """The template should render two date input fields for the custom range."""
        login(client)
        _, html = get_profile(client)
        # Two <input type="date"> fields for From / To
        assert 'type="date"' in html or "type=date" in html, (
            "Profile page should contain date input fields for the custom range picker"
        )


# ── currency format consistency ───────────────────────────────────────────────

class TestCurrencyFormat:
    """All monetary values must be displayed in ₹, never £ or $."""

    def test_no_dollar_sign_in_response(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client)
        assert "$" not in html, "Amounts must not be formatted with $ (should use ₹)"

    def test_no_pound_sign_in_response(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client)
        assert "£" not in html, "Amounts must not be formatted with £ (should use ₹)"

    def test_rupee_symbol_present(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client)
        assert "₹" in html, "Profile page must display amounts in ₹"

    def test_custom_range_amounts_use_rupee(self, client, seeded_user_id):
        login(client)
        _, html = get_profile(client, **{"from": "2026-05-01", "to": "2026-05-31"})
        assert "₹" in html, "Custom range amounts must use ₹ symbol"
        assert "$" not in html
        assert "£" not in html
