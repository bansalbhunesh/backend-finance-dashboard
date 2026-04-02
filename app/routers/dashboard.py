from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_dashboard_access
from app.models import FinancialRecord, TransactionType, User
from app.schemas import (
    CategoryTotal,
    DashboardFull,
    DashboardSummary,
    RecentActivityItem,
    TrendPoint,
    TransactionTypeEnum,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _decimal(v: object) -> Decimal:
    if v is None:
        return Decimal("0")
    return Decimal(str(v))


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    _: Annotated[User, Depends(require_dashboard_access)],
    db: Annotated[Session, Depends(get_db)],
) -> DashboardSummary:
    total_income = db.scalar(
        select(func.coalesce(func.sum(FinancialRecord.amount), 0)).where(
            FinancialRecord.type == TransactionType.income,
            FinancialRecord.is_deleted == False,
        )
    )
    total_expenses = db.scalar(
        select(func.coalesce(func.sum(FinancialRecord.amount), 0)).where(
            FinancialRecord.type == TransactionType.expense,
            FinancialRecord.is_deleted == False,
        )
    )
    count = db.scalar(select(func.count()).select_from(FinancialRecord).where(FinancialRecord.is_deleted == False)) or 0
    inc = _decimal(total_income)
    exp = _decimal(total_expenses)
    return DashboardSummary(
        total_income=inc,
        total_expenses=exp,
        net_balance=inc - exp,
        record_count=int(count),
    )


@router.get("/full", response_model=DashboardFull)
def dashboard_full(
    user: Annotated[User, Depends(require_dashboard_access)],
    db: Annotated[Session, Depends(get_db)],
    recent_limit: int = Query(default=10, ge=1, le=50),
    trend_granularity: Literal["month", "week"] = Query(default="month"),
) -> DashboardFull:
    summary = dashboard_summary(user, db)

    cat_stmt = (
        select(
            FinancialRecord.category,
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
        )
        .where(FinancialRecord.is_deleted == False)
        .group_by(FinancialRecord.category, FinancialRecord.type)
        .order_by(FinancialRecord.category, FinancialRecord.type)
    )
    category_totals = [
        CategoryTotal(
            category=row.category,
            type=TransactionTypeEnum(row.type.value),
            total=_decimal(row.total),
        )
        for row in db.execute(cat_stmt).all()
    ]

    recent_stmt = (
        select(FinancialRecord)
        .where(FinancialRecord.is_deleted == False)
        .order_by(FinancialRecord.occurred_at.desc())
        .limit(recent_limit)
    )
    recent_rows = list(db.scalars(recent_stmt).all())
    recent_activity = [
        RecentActivityItem(
            id=r.id,
            amount=_decimal(r.amount),
            type=TransactionTypeEnum(r.type.value),
            category=r.category,
            occurred_at=r.occurred_at,
            notes=r.notes,
        )
        for r in recent_rows
    ]

    if trend_granularity == "week":
        period_expr = func.strftime("%Y-%W", FinancialRecord.occurred_at)
    else:
        period_expr = func.strftime("%Y-%m", FinancialRecord.occurred_at)

    income_sum = func.sum(
        case((FinancialRecord.type == TransactionType.income, FinancialRecord.amount), else_=0)
    )
    expense_sum = func.sum(
        case((FinancialRecord.type == TransactionType.expense, FinancialRecord.amount), else_=0)
    )
    trend_stmt = (
        select(
            period_expr.label("period"),
            income_sum.label("income"),
            expense_sum.label("expense"),
        )
        .where(FinancialRecord.is_deleted == False)
        .group_by(period_expr)
        .order_by(period_expr)
    )
    monthly_trends = []
    for row in db.execute(trend_stmt).all():
        inc = _decimal(row.income)
        exp = _decimal(row.expense)
        monthly_trends.append(
            TrendPoint(period=str(row.period), income=inc, expense=exp, net=inc - exp)
        )

    return DashboardFull(
        summary=summary,
        category_totals=category_totals,
        recent_activity=recent_activity,
        monthly_trends=monthly_trends,
    )
