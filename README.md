# FreshTrack Grocery Inventory
A production-style grocery inventory system built with Python 3.11+, Flask, SQLAlchemy, Flask-Login, Flask-WTF, Jinja2, custom CSS, vanilla JavaScript, Chart.js, SQLite, and ReportLab.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
flask --app run.py seed
flask --app run.py run --debug
```
Open `http://127.0.0.1:5000`.

## Demo accounts
- Admin: `admin@freshtrack.example` / `Admin123!`
- Manager: `manager@freshtrack.example` / `Manager123!`
- Staff: `staff@freshtrack.example` / `Staff123!`

Change demo passwords before real use. Staff can browse, sell, and record stock. Managers also manage catalog data and reports. Admins have full settings, users, and delete access.

## Database
SQLite is the default. Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL for deployment. Flask-Migrate is included: `flask --app run.py db init`, then `db migrate` and `db upgrade`.

## Tests
Run `pytest`.
