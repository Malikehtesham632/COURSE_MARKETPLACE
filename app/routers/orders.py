"""
Order routes: buy a course.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.security import get_current_user
from app.core.exceptions import AppException

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "/",
    response_model=schemas.OrderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Buy a course",
)
def buy_course(
    order_in: schemas.OrderCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.query(models.Course).filter(models.Course.id == order_in.course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Domain-specific rules use the custom AppException instead of a generic HTTPException.
    if course.owner_id == current_user.id:
        raise AppException("You cannot buy your own course", status_code=400)

    existing_order = (
        db.query(models.Order)
        .filter(models.Order.buyer_id == current_user.id, models.Order.course_id == course.id)
        .first()
    )
    if existing_order:
        raise AppException("You already bought this course", status_code=400)

    new_order = models.Order(buyer_id=current_user.id, course_id=course.id, status="completed")
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order
