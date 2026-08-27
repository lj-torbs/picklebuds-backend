# PickleBuddy Backend

FastAPI scaffold aligned to the current frontend prototype and `picklebuddy.sql`.

## Run

1. Create a virtual environment
2. Install dependencies from `requirements.txt`
3. Copy `.env.example` to `.env`
4. Import `../picklebuddy.sql` into MySQL
5. Start the API:

```bash
uvicorn app.main:app --reload
```

## Current scope

- App settings and DB session wiring
- SQLAlchemy models matching the current schema
- Pydantic request/response schemas for the first booking/payment flows
- Router layout for auth, venues, bookings, pasalo, owners, and admin

Business rules like slot conflict detection, open play seat enforcement, and pasalo transfer approval still need service-layer implementation.
