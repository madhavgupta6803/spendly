import pytest
from werkzeug.security import generate_password_hash

import database.db as db_module
from app import app as flask_app
from database.db import init_db, get_db


@pytest.fixture
def app(tmp_path):
    db_path = str(tmp_path / "test.db")
    db_module.DB_PATH = db_path
    with flask_app.app_context():
        init_db()
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_user_id(app):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = cursor.lastrowid
    expenses = [
        (user_id, 350.00,  "Food",          "2026-05-01", "Lunch at café"),
        (user_id, 120.00,  "Transport",     "2026-05-03", "Uber ride"),
        (user_id, 1200.00, "Bills",         "2026-05-05", "Electricity bill"),
        (user_id, 500.00,  "Health",        "2026-05-08", "Pharmacy"),
        (user_id, 800.00,  "Entertainment", "2026-05-12", "Movie tickets"),
        (user_id, 2500.00, "Shopping",      "2026-05-15", "Clothing"),
        (user_id, 200.00,  "Other",         "2026-05-18", "Miscellaneous"),
        (user_id, 650.00,  "Food",          "2026-05-22", "Dinner with friends"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()
    return user_id


@pytest.fixture
def empty_user_id(app):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Empty User", "empty@spendly.com", generate_password_hash("pass1234")),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id
