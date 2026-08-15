"""
Application entry point: creates the FastAPI app, wires in middleware
and the custom exception handler, and plugs in every router.
"""

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, users, courses, orders
from app.core.exceptions import AppException, app_exception_handler

# Create every table that doesn't already exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Course Marketplace API",
    version="1.0.0",
    description="A REST API where instructors sell courses and students buy them.",
)

# Turns any raised AppException into a clean JSON response.
app.add_exception_handler(AppException, app_exception_handler)

# Built-in middleware: lets a frontend on a different origin call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Custom middleware: times how long each request takes to handle,
    and stamps the result onto the response as an X-Process-Time header.
    Runs on every single request, before and after the route itself.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# Each feature's routes live in their own file, plugged in here.
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(orders.router)


@app.get("/", summary="Health check", description="Confirms the API is running.")
def root():
    return {"status": "ok"}
