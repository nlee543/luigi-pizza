# Luigi's Pizzeria

The team's Python API, models, database tools and original documentation are in `backend/`.

Run the existing API from that directory:

```sh
cd backend
python -m pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

See `backend/README.md` for the original authentication, seeding and migration instructions.

## Frontend prototype

Run `node scripts/server.js` from the repository root and open http://localhost:5173.
The HTML/CSS/vanilla-JavaScript interface includes customer ordering and a staff demonstration.
This standalone preview stores fictional demo activity in this browser; it does not connect to the API.
Employee demo login is Luigi / Pizza. Payments and automated support replies are simulated.
