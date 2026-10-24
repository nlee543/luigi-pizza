# Luigi's Pizzeria

The team's Python API, models, database tools and original documentation are in `backend/`.

Run the existing API from that directory:

```sh
cd backend
python -m pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

See `backend/README.md` for the original authentication, seeding and migration instructions.
