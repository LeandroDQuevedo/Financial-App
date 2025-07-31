# app/api/routes.py
from flask import Blueprint, jsonify
from ..core import models, services
from sqlalchemy import func
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/expense_by_category/<int:year>/<int:month>')
def api_expense_by_category(year, month):
    expenses = {}
    cash_q = models.db.session.query(models.Category.name, func.sum(models.Transaction.amount)).join(models.Transaction.category).filter(
        models.Transaction.type == 'despesa', 
        func.extract('month', models.Transaction.date) == month, 
        func.extract('year', models.Transaction.date) == year
    ).group_by(models.Category.name).all()
    for name, amount in cash_q:
        expenses[name] = expenses.get(name, 0) + amount

    card_q = models.db.session.query(models.Category.name, func.sum(models.Installment.amount)).join(models.CardPurchase).join(models.Category).filter(
        models.Installment.invoice_year == year, 
        models.Installment.invoice_month == month
    ).group_by(models.Category.name).all()
    for name, amount in card_q:
        expenses[name] = expenses.get(name, 0) + amount

    return jsonify({'labels': list(expenses.keys()), 'data': list(expenses.values())})

@api_bp.route('/api/check_goal_reminder')
def check_goal_reminder():
    if not models.Goal.query.filter(models.Goal.current_amount < models.Goal.target_amount).first():
        return jsonify({'show_reminder': False})

    today = datetime.now(timezone.utc)
    first_day = today.replace(day=1)
    business_days_count = 0
    fifth_business_day = None

    current_day = first_day
    while current_day.month == first_day.month:
        if current_day.weekday() < 5: # 0-4 são Seg-Sex
            business_days_count += 1
        if business_days_count == 5:
            fifth_business_day = current_day
            break
        current_day += relativedelta(days=1)

    show_popup = fifth_business_day and today.day >= fifth_business_day.day

    return jsonify({'show_reminder': show_popup, 'current_month_year': today.strftime('%Y-%m')})