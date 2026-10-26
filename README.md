# CalorieTracker BI Dashboard

[![CI](https://github.com/aryann003/calorieTracker/actions/workflows/ci.yml/badge.svg)](https://github.com/aryann003/calorieTracker/actions/workflows/ci.yml)

A full-stack calorie tracking and nutrition analytics project built with **Django**, **Python**, **PostgreSQL**, and **Power BI**.

The Django web app allows users to log food intake, track calories and macronutrients, manage health profile details, and record weight progress. A custom Django export command converts the database records into clean CSV files, which are then used in Power BI to build interactive Daily and Period analytics dashboards.

---

## Live Demo

https://calorietracker-2-auqx.onrender.com

Demo account (pre-filled with three weeks of food and weight logs): username `demo`, password `DemoPass123!`.
The app runs on a free tier, so the first request after a quiet period can take about a minute.

## Features

### Django Web App

- User registration and login
- Add food items with calories and macronutrients
- Log consumed food with quantity in grams
- Track meal type such as breakfast, lunch, dinner, and snacks
- Manage user health profile
- Calculate BMI, BMR, TDEE, and personalized nutrition targets
- Add and track weight logs
- Quantity-based calorie and macro calculation
- Shared catalogue of 47 common foods (plus your own private foods)

### Power BI Dashboard

- Daily nutrition analysis
- Period-based nutrition analysis
- Calories vs target tracking
- Macro goal percentage tracking
- Meal-wise calorie analysis
- Food category analysis
- Top foods by calorie contribution
- Current weight and weight progress tracking
- Date-based filtering using Power BI Date Table
- DAX measures for daily and period-level insights

---

## Tech Stack

| Area            | Technology                                        |
| --------------- | ------------------------------------------------- |
| Backend         | Django, Python                                    |
| Database        | PostgreSQL (Neon) in production, SQLite locally   |
| Frontend        | HTML, CSS, Bootstrap                              |
| Data Export     | Python CSV, Django Management Command             |
| Analytics       | Power BI                                          |
| BI Modeling     | Relationships, Date Table, DAX                    |
| Testing         | Pytest, pytest-django, coverage (100+ tests)      |
| CI / Delivery   | GitHub Actions (PostgreSQL service), Docker       |
| Hosting         | Render, WhiteNoise, Gunicorn                      |
| Version Control | Git, GitHub                                       |

--------------- | ------------------------------------- |
| Backend         | Django, Python                        |
| Database        | SQLite                                |
| Frontend        | HTML, CSS, Bootstrap                  |
| Data Export     | Python CSV, Django Management Command |
| Analytics       | Power BI                              |
| BI Modeling     | Relationships, Date Table, DAX        |
| Version Control | Git, GitHub                           |

---

## Project Architecture

```text
Django Web App
        ↓
PostgreSQL (Neon)
        ↓
Python Export Command
        ↓
Clean CSV Files
        ↓
Power BI Dashboard
```

The Django application is used for data entry and tracking. Power BI is used as the analytics and reporting layer.

---

## Screenshots

### Landing Page

![Landing Page](screenshots/landing-page.png)

### Django Dashboard

![Django Dashboard](screenshots/django-dashboard-1.png)

### Profile Page

![Profile Page](screenshots/profile-page.png)

### Weight Log Page

![Weight Log Page](screenshots/weight-log.png)

### Power BI Daily View

![Power BI Daily View](screenshots/powerbi-daily-view.png)

### Power BI Period View

![Power BI Period View](screenshots/powerbi-period-view.png)

---

## Power BI Analytics

The Power BI report contains two main views:

### Daily View

Used for single-day analysis.

It shows:

- Total calories consumed
- Target calories
- Remaining calories
- Macro goal progress
- Meal-wise calories
- Food category distribution
- Food log details

### Period View

Used for multi-day or weekly analysis.

It shows:

- Logged days
- Total calories
- Average daily calories
- Period target calories
- Period calorie goal percentage
- Calories trend
- Weight progress
- Top foods and category insights

---

## Data Export

A custom Django management command exports clean CSV files for Power BI.

Export all data:

```bash
python manage.py export_powerbi_data
```

Export data for a specific user:

```bash
python manage.py export_powerbi_data --username aryan
```

Generated files:

```text
foods.csv
consumption_logs.csv
user_profiles.csv
weight_logs.csv
daily_nutrition_summary.csv
```

The exported CSV files are generated data files and are not committed to Git.

---

## Power BI Data Model

Main tables used in Power BI:

```text
foods
consumption_logs
user_profiles
weight_logs
daily_nutrition_summary
DateTable
```

Main relationships:

```text
consumption_logs[food_id] → foods[food_id]
consumption_logs[user_id] → user_profiles[user_id]
daily_nutrition_summary[user_id] → user_profiles[user_id]
weight_logs[user_id] → user_profiles[user_id]
DateTable[Date] → daily_nutrition_summary[date]
DateTable[Date] → consumption_logs[date]
DateTable[Date] → weight_logs[date]
```

---

## Key DAX Measures

```DAX
Total Calories = SUM(daily_nutrition_summary[total_calories])
```

```DAX
Target Calories = MAX(user_profiles[target_calories])
```

```DAX
Calories Remaining = [Target Calories] - [Total Calories]
```

```DAX
Calories Goal % = DIVIDE([Total Calories], [Target Calories], 0)
```

```DAX
Logged Days = DISTINCTCOUNT(daily_nutrition_summary[date])
```

```DAX
Average Daily Calories = DIVIDE([Total Calories], [Logged Days], 0)
```

```DAX
Period Target Calories = [Target Calories] * [Logged Days]
```

```DAX
Period Calories Goal % = DIVIDE([Total Calories], [Period Target Calories], 0)
```

---

## How to Run Locally

### With Docker (PostgreSQL included)

```bash
docker compose up --build
docker compose exec web python manage.py seed_demo
```

Open http://localhost:8000 and sign in as `demo` / `DemoPass123!`.

### Without Docker

```bash
git clone https://github.com/aryann003/calorieTracker.git
cd calorieTracker
python -m venv venv
source venv/bin/activate          # Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd mysite
cp ../.env.example .env           # then edit; DEBUG=True is fine for local use
python manage.py migrate
python manage.py seed_foods       # shared catalogue of 47 foods
python manage.py seed_demo        # optional demo account with sample data
python manage.py runserver
```

Open http://127.0.0.1:8000/. Without `DATABASE_URL` the app uses a local SQLite file.

---

## Power BI Refresh Workflow

After adding new data in Django:

```bash
python manage.py export_powerbi_data --username aryan
```

Then open Power BI Desktop and click:

```text
Home → Refresh
```

---

## Testing

```bash
pip install -r requirements-dev.txt
cd mysite
pytest --cov
```

The suite needs PostgreSQL (`DATABASE_URL` defaults to `postgres://calorie:calorie@localhost:5432/calorie` in `pytest.ini`). It covers:

- the nutrition formulas (BMI, BMR, TDEE, calorie and macro targets), checked against hand-calculated values
- logging, totals and goals on the dashboard
- authorization: users can only see, log and delete their own data
- input validation (negative or impossible values, `nan`, `inf`)
- timezone handling, weight tracking, the Power BI export, and the seed commands
- a query-count test that fails if the dashboard starts running one query per entry

CI runs it on every push against a PostgreSQL service container.

---

## Correctness and Security Notes

- **Validated input:** quantities must be finite and between 0 and 10,000 g; foods and profile values have realistic ranges; macros cannot exceed 100 g per 100 g.
- **CSRF-safe actions:** removing an entry and logging out are POST-only with CSRF tokens.
- **Data isolation:** a user can only log foods they own or that are shared, and only delete their own entries.
- **User's calendar day:** "today" follows `TIME_ZONE` (default `Asia/Kolkata`), not UTC.
- **Current weight** is the most recent entry by date, so backfilling an old weigh-in does not overwrite it.
- **Fewer queries:** the dashboard loads food details with `select_related`, so it runs a constant 4 queries instead of one extra query per logged item.
- **Safe defaults:** `DEBUG` is off unless enabled, and the app refuses to start without a `SECRET_KEY` in production.

---

## Deployment (Render + Neon)

`render.yaml` defines the web service and `build.sh` the build (install, collect static files, migrate, seed the shared foods and, if `SEED_DEMO=true`, the demo account). The database is an external PostgreSQL (Neon) so data persists across redeploys.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string (set in the Render dashboard) |
| `SECRET_KEY` | Generated by the blueprint |
| `DEBUG` | `False` in production |
| `SEED_DEMO` | `true` creates the demo account on deploy (skipped if it exists) |
| `TIME_ZONE` | Optional, default `Asia/Kolkata` |

---

## Known Limitations

- Nutrition values in the shared catalogue are approximate (per 100 g, from common food tables).
- Targets use a fixed 25% protein / 50% carbs / 25% fat split, and the `other` gender option uses the male BMR constant.
- The free tier sleeps when idle; Power BI refresh is manual (run the export, then Refresh).

## Future Improvements

- User-facing charts inside Django using Chart.js
- Connect Power BI directly to PostgreSQL
- Scheduled refresh and weekly nutrition reports
- Password reset by email, and a role-based admin analytics dashboard

---

## Author

**Aryan Katiyar**

GitHub: [aryann003](https://github.com/aryann003)
