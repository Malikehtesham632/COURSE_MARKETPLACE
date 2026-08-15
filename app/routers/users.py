"""
User routes: see your own profile, the courses you created, and the
courses you've bought. All three require a valid login.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=schemas.UserOut,
    summary="Get my profile",
)
def get_my_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get(
    "/me/courses",
    response_model=list[schemas.CourseOut],
    summary="Get the courses I created",
)
def get_my_courses(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(models.Course).filter(models.Course.owner_id == current_user.id).all()


@router.get(
    "/me/purchases",
    response_model=list[schemas.OrderOut],
    summary="Get the courses I've bought",
)
def get_my_purchases(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(models.Order).filter(models.Order.buyer_id == current_user.id).all()
