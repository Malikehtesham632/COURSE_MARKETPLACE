# Course Marketplace API

A REST API for a course marketplace, built with FastAPI. Instructors register,
log in, and sell courses. Students register, log in, and buy them. Every
protected action is secured with a JWT token, and users can only edit or
delete their own data.

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

Run it:

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to try every endpoint from the browser.

## Project structure

```
app/
  main.py                creates the app, wires in middleware, includes routers
  database.py             engine, SessionLocal, Base, get_db
  models.py                SQLAlchemy models (the tables)
  schemas.py                Pydantic schemas (request/response shapes)
  core/
    config.py                 settings, loaded with pydantic-settings
    security.py                 password hashing, JWT helpers, get_current_user
    exceptions.py                  the custom AppException + its handler
  routers/
    auth.py                        register, login
    users.py                        profile, my courses, my purchases
    courses.py                       the main resource - full CRUD
    orders.py                          buy a course
```

## How login works

1. `POST /auth/register` — creates an account. Passwords are hashed with
   bcrypt before being stored; the real password is never saved.
2. `POST /auth/login` — checks email and password, returns a signed JWT.
3. Every protected route needs that token in the header:
   `Authorization: Bearer <your_token>`

In the `/docs` page, click **Authorize** and paste just the token — no
username/password form.

## Endpoints

| Method | Path                | What it does                              | Login | Notes |
|--------|---------------------|--------------------------------------------|-------|-------|
| POST   | /auth/register      | Create a new account                       | No    | Custom validation on password strength |
| POST   | /auth/login         | Get a JWT token                             | No    | |
| GET    | /users/me           | See your own profile                        | Yes   | |
| GET    | /users/me/courses   | See courses you created                     | Yes   | |
| GET    | /users/me/purchases | See courses you've bought                   | Yes   | |
| GET    | /courses/           | List courses                                | No    | Query params: `search`, `skip`, `limit`; optional `X-Client` header |
| GET    | /courses/{id}       | Get one course                              | No    | |
| POST   | /courses/           | Create a course                             | Yes   | Instructors only (3-layer dependency); custom validation on price |
| PUT    | /courses/{id}       | Replace a course (all fields required)      | Yes   | Owner only |
| PATCH  | /courses/{id}       | Partially update a course (fields optional) | Yes   | Owner only |
| DELETE | /courses/{id}       | Delete a course                             | Yes   | Owner only, returns 204 |
| POST   | /orders/            | Buy a course                                | Yes   | Custom `AppException` for business rules |

## What's demonstrated here (for grading reference)

- **Custom validation** — `UserCreate.password` and `CourseCreate.price` both
  reject bad input with a Pydantic `@field_validator`, before the database is
  ever touched.
- **Custom exception** — `AppException` (in `core/exceptions.py`) is used for
  domain rules like "you can't buy your own course," separate from the
  generic `HTTPException` used for 404/403 errors.
- **Nested data models** — `CourseOut` embeds a nested `OwnerOut`; `OrderOut`
  embeds a full nested `CourseOut`.
- **All parameter types** — path params (`course_id`), query params (`search`,
  `skip`, `limit` on course listing), a header param (`X-Client`), and body
  params (every POST/PUT/PATCH).
- **3-layer dependency chain** — creating a course depends on
  `get_current_instructor`, which itself depends on `get_current_user`, which
  depends on `get_db`. `get_current_user` alone is reused across `users`,
  `courses`, and `orders` routers.
- **Custom middleware** — `add_process_time_header` in `main.py` times every
  request and adds an `X-Process-Time` response header, alongside the
  built-in `CORSMiddleware`.
- **Proper status codes** — `201` on every create, `204` (no body) on delete,
  `422` on validation errors, `401`/`403`/`404`/`400` used correctly
  throughout.

## Database

Uses PostgreSQL via SQLAlchemy. For quick local testing without a real
database, `DATABASE_URL` can be set to `sqlite:///./test.db` instead — the
code detects this automatically in `database.py`.

## Deploying

1. Push this folder to GitHub (`.env` is excluded via `.gitignore`).
2. On your host, set the start command:
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Set `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, and
   `ACCESS_TOKEN_EXPIRE_MINUTES` as environment variables on the host.

**Note on the database driver:** this project uses `psycopg2-binary`, the
standard PostgreSQL driver. Some hosts (Railway's default builder, in
particular) are missing a system library it depends on
(`libpq.so.5`), causing an `ImportError` on deploy. If that happens, the
fix is switching the driver to `pg8000` (a pure-Python driver with no
system dependency) in `requirements.txt` and the connection string prefix
in `database.py` — ask for help making that swap if you hit this.
