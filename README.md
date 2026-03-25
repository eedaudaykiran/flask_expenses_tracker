# Expense Tracker

A Flask web application for managing personal finances.

## Features

- User registration and login
- Add, edit, delete expenses
- Filter expenses by category and date range
- Set monthly budgets per category
- Visual reports with charts (pie and line)

## Installation

1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run the app: `python run.py`
6. Visit `http://127.0.0.1:5000`

## Configuration

Edit `config.py` or set environment variables:
- `SECRET_KEY`: a secret key for sessions
- `DATABASE_URL`: database URI (defaults to SQLite)