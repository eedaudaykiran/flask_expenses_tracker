from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Category, Expense, Budget
from app.forms import LoginForm, RegistrationForm, ExpenseForm, BudgetForm
from datetime import datetime, date
from sqlalchemy import func
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)
budget_bp = Blueprint('budget', __name__)
reports_bp = Blueprint('reports', __name__)

# ---------- Authentication ----------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # Create default categories for the user
        default_categories = ['Food', 'Transport', 'Entertainment', 'Utilities', 'Rent', 'Shopping', 'Healthcare', 'Other']
        for cat in default_categories:
            category = Category(name=cat, user_id=user.id)
            db.session.add(category)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# ---------- Main ----------
@main_bp.route('/')
def index():
    """Root URL: redirect to dashboard if logged in, else to login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get current month and year
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Total expenses this month
    total_spent = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        func.extract('month', Expense.date) == current_month,
        func.extract('year', Expense.date) == current_year
    ).scalar() or 0.0

    # Get budgets for this month
    budgets = Budget.query.filter_by(user_id=current_user.id, month=current_month, year=current_year).all()
    total_budget = sum(b.amount_limit for b in budgets) if budgets else 0

    # Recent expenses
    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5).all()

    return render_template('dashboard.html',
                           total_spent=total_spent,
                           total_budget=total_budget,
                           recent_expenses=recent_expenses)

@main_bp.route('/expenses')
@login_required
def list_expenses():
    category_id = request.args.get('category', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Expense.query.filter_by(user_id=current_user.id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    expenses = query.order_by(Expense.date.desc()).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('expenses.html', expenses=expenses, categories=categories)

@main_bp.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    # Populate category choices
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form.category.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        expense = Expense(
            amount=form.amount.data,
            date=form.date.data,
            description=form.description.data,
            category_id=form.category.data,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('main.list_expenses'))
    return render_template('add_expense.html', form=form)

@main_bp.route('/expense/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash('You do not have permission to edit this expense.', 'danger')
        return redirect(url_for('main.list_expenses'))

    form = ExpenseForm()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form.category.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        expense.amount = form.amount.data
        expense.date = form.date.data
        expense.description = form.description.data
        expense.category_id = form.category.data
        db.session.commit()
        flash('Expense updated successfully.', 'success')
        return redirect(url_for('main.list_expenses'))
    elif request.method == 'GET':
        form.amount.data = expense.amount
        form.date.data = expense.date
        form.description.data = expense.description
        form.category.data = expense.category_id
    return render_template('edit_expense.html', form=form, expense=expense)

@main_bp.route('/expense/delete/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash('You do not have permission to delete this expense.', 'danger')
        return redirect(url_for('main.list_expenses'))
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('main.list_expenses'))

# ---------- Budget ----------
@budget_bp.route('/budgets', methods=['GET', 'POST'])
@login_required
def manage_budgets():
    form = BudgetForm()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form.category.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        # Check if budget already exists for this category, month, year
        existing = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=form.category.data,
            month=form.month.data,
            year=form.year.data
        ).first()
        if existing:
            existing.amount_limit = form.amount_limit.data
            flash('Budget updated.', 'success')
        else:
            budget = Budget(
                month=form.month.data,
                year=form.year.data,
                amount_limit=form.amount_limit.data,
                category_id=form.category.data,
                user_id=current_user.id
            )
            db.session.add(budget)
            flash('Budget set.', 'success')
        db.session.commit()
        return redirect(url_for('budget.manage_budgets'))

    # List budgets
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    # For each budget, calculate spent amount
    budgets_data = []
    for b in budgets:
        spent = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.category_id == b.category_id,
            func.extract('month', Expense.date) == b.month,
            func.extract('year', Expense.date) == b.year
        ).scalar() or 0.0
        budgets_data.append({
            'budget': b,
            'spent': spent,
            'remaining': b.amount_limit - spent,
            'percent': (spent / b.amount_limit) * 100 if b.amount_limit > 0 else 0
        })
    return render_template('budgets.html', form=form, budgets_data=budgets_data)

# ---------- Reports ----------
@reports_bp.route('/reports')
@login_required
def reports():
    now = datetime.now()
    return render_template('reports.html', now=now)

@reports_bp.route('/api/chart-data')
@login_required
def chart_data():
    # Get current month and year
    now = datetime.now()
    month = request.args.get('month', now.month, type=int)
    year = request.args.get('year', now.year, type=int)

    # Spending by category
    category_spending = db.session.query(
        Category.name,
        func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        Expense.user_id == current_user.id,
        func.extract('month', Expense.date) == month,
        func.extract('year', Expense.date) == year
    ).group_by(Category.name).all()

    labels = [item[0] for item in category_spending]
    values = [float(item[1]) for item in category_spending]

    # Daily spending for line chart
    daily_spending = db.session.query(
        Expense.date,
        func.sum(Expense.amount).label('daily_total')
    ).filter(
        Expense.user_id == current_user.id,
        func.extract('month', Expense.date) == month,
        func.extract('year', Expense.date) == year
    ).group_by(Expense.date).order_by(Expense.date).all()

    dates = [d[0].strftime('%Y-%m-%d') for d in daily_spending]
    daily_totals = [float(d[1]) for d in daily_spending]

    return jsonify({
        'pie_labels': labels,
        'pie_values': values,
        'line_labels': dates,
        'line_values': daily_totals
    })