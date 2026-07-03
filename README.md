# CalorieTracker BI Dashboard

A full-stack calorie tracking and nutrition analytics project built with **Django**, **Python**, **SQLite**, and **Power BI**.

The Django web app allows users to log food intake, track calories and macronutrients, manage health profile details, and record weight progress. A custom Django export command converts the database records into clean CSV files, which are then used in Power BI to build interactive Daily and Period analytics dashboards.

---

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

| Area            | Technology                            |
| --------------- | ------------------------------------- |
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
SQLite Database
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

### 1. Clone the repository

```bash
git clone https://github.com/aryann003/calorieTracker.git
cd calorieTracker
```

### 2. Go to Django project folder

```bash
cd mysite
```

### 3. Create virtual environment

```bash
python -m venv venv
```

### 4. Activate virtual environment

For Windows PowerShell:

```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Start server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

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

## Future Improvements

- Deploy Django app with PostgreSQL
- Add user-facing charts inside Django using Chart.js
- Connect Power BI directly to PostgreSQL
- Add scheduled refresh
- Add weekly nutrition reports
- Add role-based admin analytics dashboard

---

## Author

**Aryan Katiyar**

GitHub: [aryann003](https://github.com/aryann003)
