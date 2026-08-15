"""
Course routes: browse, create, fully replace, partially update, and
delete courses.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.security import get_current_user, get_current_instructor

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get(
    "/",
    response_model=list[schemas.CourseOut],
    summary="List courses",
    description="Returns courses, with pagination and an optional title search. Public - no login needed.",
)
def list_courses(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="How many results to skip, for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results to return"),
    search: Optional[str] = Query(None, description="Only return courses whose title contains this text"),
    x_client: Optional[str] = Header(None, description="Optional client name, accepted for logging/analytics only"),
):
    query = db.query(models.Course)
    if search:
        query = query.filter(models.Course.title.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


@router.get(
    "/{course_id}",
    response_model=schemas.CourseOut,
    summary="Get one course",
    description="Public - no login needed.",
)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.post(
    "/",
    response_model=schemas.CourseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a course",
    description="Only logged-in instructors can create a course.",
)
def create_course(
    course_in: schemas.CourseCreate,
    # 3-layer dependency chain: get_db -> get_current_user -> get_current_instructor
    current_user: models.User = Depends(get_current_instructor),
    db: Session = Depends(get_db),
):
    new_course = models.Course(
        title=course_in.title,
        description=course_in.description,
        price=course_in.price,
        owner_id=current_user.id,
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


@router.put(
    "/{course_id}",
    response_model=schemas.CourseOut,
    summary="Replace a course",
    description="Full replace - every field is required, matching PUT semantics. Only the owner can do this.",
)
def replace_course(
    course_id: int,
    course_in: schemas.CourseReplace,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = _get_owned_course(course_id, current_user, db)
    course.title = course_in.title
    course.description = course_in.description
    course.price = course_in.price
    db.commit()
    db.refresh(course)
    return course


@router.patch(
    "/{course_id}",
    response_model=schemas.CourseOut,
    summary="Partially update a course",
    description="Partial update - only the fields you send are changed, matching PATCH semantics. Only the owner can do this.",
)
def update_course(
    course_id: int,
    course_in: schemas.CourseUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = _get_owned_course(course_id, current_user, db)
    if course_in.title is not None:
        course.title = course_in.title
    if course_in.description is not None:
        course.description = course_in.description
    if course_in.price is not None:
        course.price = course_in.price
    db.commit()
    db.refresh(course)
    return course


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a course",
    description="Only the owner can do this.",
)
def delete_course(
    course_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = _get_owned_course(course_id, current_user, db)
    db.delete(course)
    db.commit()
    return None


def _get_owned_course(course_id: int, current_user: models.User, db: Session) -> models.Course:
    """Shared helper: fetches a course and confirms the current user owns it."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your course")
    return course
