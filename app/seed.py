from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FinancialRecord, Role, TransactionType, User
from app.security import hash_password


def seed_if_empty(db: Session) -> None:
    if db.scalars(select(User).limit(1)).first() is not None:
        return

    now = datetime.now(timezone.utc)
    users = [
        User(
            email="admin@example.com",
            hashed_password=hash_password("Admin12345!"),
            full_name="Admin User",
            role=Role.admin,
            is_active=True,
        ),
        User(
            email="analyst@example.com",
            hashed_password=hash_password("Analyst12345!"),
            full_name="Analyst User",
            role=Role.analyst,
            is_active=True,
        ),
        User(
            email="viewer@example.com",
            hashed_password=hash_password("Viewer12345!"),
            full_name="Viewer User",
            role=Role.viewer,
            is_active=True,
        ),
    ]
    db.add_all(users)
    db.commit()
    for u in users:
        db.refresh(u)

    admin_id = users[0].id
    sample = [
        FinancialRecord(
            amount="4500.00",
            type=TransactionType.income,
            category="salary",
            occurred_at=now - timedelta(days=60),
            notes="Monthly salary",
            created_by_user_id=admin_id,
        ),
        FinancialRecord(
            amount="1200.50",
            type=TransactionType.expense,
            category="housing",
            occurred_at=now - timedelta(days=58),
            notes="Rent",
            created_by_user_id=admin_id,
        ),
        FinancialRecord(
            amount="320.00",
            type=TransactionType.expense,
            category="utilities",
            occurred_at=now - timedelta(days=45),
            notes="Electricity",
            created_by_user_id=admin_id,
        ),
        FinancialRecord(
            amount="800.00",
            type=TransactionType.income,
            category="freelance",
            occurred_at=now - timedelta(days=30),
            notes="Contract work",
            created_by_user_id=admin_id,
        ),
        FinancialRecord(
            amount="95.40",
            type=TransactionType.expense,
            category="food",
            occurred_at=now - timedelta(days=7),
            notes="Groceries",
            created_by_user_id=admin_id,
        ),
        FinancialRecord(
            amount="42.10",
            type=TransactionType.expense,
            category="food",
            occurred_at=now - timedelta(days=1),
            notes="Coffee and lunch",
            created_by_user_id=admin_id,
        ),
    ]
    db.add_all(sample)
    db.commit()
