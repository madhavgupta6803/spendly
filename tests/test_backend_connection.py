from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


# ── get_user_by_id ────────────────────────────────────────────────────────────

def test_get_user_by_id_valid(app, seeded_user_id):
    user = get_user_by_id(seeded_user_id)
    assert user is not None
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"
    assert "member_since" in user
    assert user["member_since"] != ""


def test_get_user_by_id_nonexistent(app):
    assert get_user_by_id(99999) is None


# ── get_summary_stats ─────────────────────────────────────────────────────────

def test_get_summary_stats_with_expenses(app, seeded_user_id):
    stats = get_summary_stats(seeded_user_id)
    assert stats["total_spent"] == "₹6,320"
    assert stats["transaction_count"] == 8
    assert stats["top_category"] == "Shopping"


def test_get_summary_stats_no_expenses(app, empty_user_id):
    stats = get_summary_stats(empty_user_id)
    assert stats["total_spent"] == "₹0"
    assert stats["transaction_count"] == 0
    assert stats["top_category"] == "—"


# ── get_recent_transactions ───────────────────────────────────────────────────

def test_get_recent_transactions_with_expenses(app, seeded_user_id):
    txns = get_recent_transactions(seeded_user_id)
    assert len(txns) == 8
    # Newest first: 2026-05-22
    assert txns[0]["date"] == "22 May 2026"
    assert txns[0]["description"] == "Dinner with friends"
    assert txns[0]["category"] == "Food"
    assert txns[0]["amount"] == "₹650"
    # Oldest last: 2026-05-01
    assert txns[-1]["date"] == "1 May 2026"
    for t in txns:
        assert "date" in t
        assert "description" in t
        assert "category" in t
        assert "amount" in t
        assert t["amount"].startswith("₹")


def test_get_recent_transactions_no_expenses(app, empty_user_id):
    assert get_recent_transactions(empty_user_id) == []


def test_get_recent_transactions_limit(app, seeded_user_id):
    txns = get_recent_transactions(seeded_user_id, limit=3)
    assert len(txns) == 3


# ── get_category_breakdown ────────────────────────────────────────────────────

def test_get_category_breakdown_with_expenses(app, seeded_user_id):
    cats = get_category_breakdown(seeded_user_id)
    assert len(cats) == 7
    # Ordered by amount descending — Shopping is highest at ₹2,500
    assert cats[0]["name"] == "Shopping"
    assert cats[0]["amount"] == "₹2,500"
    # pct values are integers summing to exactly 100
    for c in cats:
        assert isinstance(c["pct"], int)
        assert "name" in c
        assert "amount" in c
        assert c["amount"].startswith("₹")
    assert sum(c["pct"] for c in cats) == 100


def test_get_category_breakdown_no_expenses(app, empty_user_id):
    assert get_category_breakdown(empty_user_id) == []


# ── /profile route ────────────────────────────────────────────────────────────

def test_profile_unauthenticated(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_authenticated(client, seeded_user_id):
    # Log in via the login route
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/profile")
    assert response.status_code == 200
    html = response.data.decode()
    assert "Demo User" in html
    assert "demo@spendly.com" in html
    assert "₹" in html
    assert "₹6,320" in html
    assert "Shopping" in html
