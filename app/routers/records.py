from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin, require_analyst_or_admin
from app.models import FinancialRecord, TransactionType, User
from app.schemas import (
    FinancialRecordCreate,
    FinancialRecordResponse,
    FinancialRecordUpdate,
    TransactionTypeEnum,
)

router = APIRouter(prefix="/records", tags=["records"])


@router.get("", response_model=list[FinancialRecordResponse])
def list_records(
    _: Annotated[User, Depends(require_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
    date_from: datetime | None = Query(default=None, description="Filter occurred_at >= date_from (inclusive)"),
    date_to: datetime | None = Query(default=None, description="Filter occurred_at <= date_to (inclusive)"),
    category: str | None = Query(default=None, max_length=128),
    type: TransactionTypeEnum | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[FinancialRecord]:
    stmt = select(FinancialRecord).order_by(FinancialRecord.occurred_at.desc())
    if date_from is not None:
        stmt = stmt.where(FinancialRecord.occurred_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(FinancialRecord.occurred_at <= date_to)
    if category is not None:
        stmt = stmt.where(FinancialRecord.category == category.strip())
    if type is not None:
        stmt = stmt.where(FinancialRecord.type == TransactionType(type.value))
    stmt = stmt.offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/{record_id}", response_model=FinancialRecordResponse)
def get_record(
    record_id: int,
    _: Annotated[User, Depends(require_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> FinancialRecord:
    record = db.get(FinancialRecord, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


@router.post("", response_model=FinancialRecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    body: FinancialRecordCreate,
    user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> FinancialRecord:
    rec = FinancialRecord(
        amount=body.amount,
        type=TransactionType(body.type.value),
        category=body.category.strip(),
        occurred_at=body.occurred_at,
        notes=body.notes,
        created_by_user_id=user.id,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.patch("/{record_id}", response_model=FinancialRecordResponse)
def update_record(
    record_id: int,
    body: FinancialRecordUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> FinancialRecord:
    record = db.get(FinancialRecord, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    if body.model_dump(exclude_unset=True) == {}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    if body.amount is not None:
        record.amount = body.amount
    if body.type is not None:
        record.type = TransactionType(body.type.value)
    if body.category is not None:
        record.category = body.category.strip()
    if body.occurred_at is not None:
        record.occurred_at = body.occurred_at
    if body.notes is not None:
        record.notes = body.notes

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    record = db.get(FinancialRecord, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    db.delete(record)
    db.commit()
