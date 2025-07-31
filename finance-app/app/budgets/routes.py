# app/budgets/routes.py

from flask import Blueprint, render_template, request, redirect, url_for # type: ignore
from app.core import models
from app import db
from datetime import datetime, timezone
from sqlalchemy import func # type: ignore

# Definimos o novo blueprint 'budgets_bp'
budgets_bp = Blueprint(
    'budgets',
    __name__,
    template_folder='templates',
    url_prefix='/budgets' # Todas as rotas aqui começarão com /budgets
)

@budgets_bp.route('/', methods=['GET', 'POST'])
def manage_budgets():
    now = datetime.now(timezone.utc)
    if request.method == 'POST':
        category_id = request.form.get('category')
        amount = float(request.form.get('amount'))
        month = int(request.form.get('month'))
        year = int(request.form.get('year'))

        existing_budget = models.Budget.query.filter_by(
            category_id=category_id, 
            month=month, 
            year=year
        ).first()

        if existing_budget:
            existing_budget.amount = amount
        else:
            new_budget = models.Budget(
                category_id=category_id, 
                amount=amount, 
                month=month, 
                year=year
            )
            db.session.add(new_budget)
        
        db.session.commit()
        return redirect(url_for('budgets.manage_budgets'))

    budgets = models.Budget.query.filter_by(month=now.month, year=now.year).all()
    
    return render_template(
        'budgets/budgets.html', 
        budgets={b.category_id: b.amount for b in budgets}, 
        current_month=now.month, 
        current_year=now.year
    )

@budgets_bp.route('/categories', methods=['POST'])
def manage_categories():
    category_name = request.form.get('name')
    if category_name:
        existing_category = models.Category.query.filter(
            func.lower(models.Category.name) == func.lower(category_name)
        ).first()
        if not existing_category:
            new_category = models.Category(name=category_name)
            db.session.add(new_category)
            db.session.commit()
            
    return redirect(url_for('budgets.manage_budgets'))