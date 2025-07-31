# app/goals/routes.py

from flask import Blueprint, render_template, request, redirect, url_for
from app.core import models
from app import db
# Importamos 'datetime' e 'timezone'
from datetime import datetime, timezone
# Importamos o 'relativedelta' para o cálculo
from dateutil.relativedelta import relativedelta

# Definimos o novo blueprint 'goals_bp'
goals_bp = Blueprint(
    'goals',
    __name__,
    template_folder='templates',
    url_prefix='/goals'
)

@goals_bp.route('/', methods=['GET', 'POST'])
def manage_goals():
    if request.method == 'POST':
        target_date_str = request.form.get('target_date')
        # Ao guardar, garantimos que a data tem fuso horário UTC
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc) if target_date_str else None
        
        models.db.session.add(models.Goal(
            name=request.form.get('name'),
            target_amount=float(request.form.get('target_amount')),
            target_date=target_date
        ))
        models.db.session.commit()
        return redirect(url_for('goals.manage_goals'))
    
    goals_with_recommendation = []
    all_goals = models.Goal.query.order_by(models.Goal.creation_date.desc()).all()

    for goal in all_goals:
        recommendation = 0
        if goal.target_date and goal.target_amount > goal.current_amount:
            # AQUI ESTÁ A CORREÇÃO: Usamos datetime.utcnow() para a comparação
            now_naive = datetime.utcnow()
            if goal.target_date > now_naive:
                months_left = relativedelta(goal.target_date, now_naive).months + \
                              relativedelta(goal.target_date, now_naive).years * 12
                if months_left > 0:
                    recommendation = (goal.target_amount - goal.current_amount) / months_left
        goals_with_recommendation.append({'goal': goal, 'recommendation': recommendation})
    
    return render_template('goals/goals.html', goals_data=goals_with_recommendation)

@goals_bp.route('/deposit/<int:goal_id>', methods=['POST'])
def deposit_to_goal(goal_id):
    goal = models.Goal.query.get_or_404(goal_id)
    amount = float(request.form.get('amount'))

    if amount > 0:
        goal.current_amount += amount
        
        goals_category = models.Category.query.filter_by(name="Metas").first()
        if not goals_category:
            goals_category = models.Category(name="Metas")
            db.session.add(goals_category)
            db.session.flush()
        
        models.db.session.add(models.Transaction(
            description=f"Depósito para meta: {goal.name}", 
            amount=amount, 
            type='despesa', 
            category_id=goals_category.id
        ))
        models.db.session.commit()
        
    return redirect(url_for('goals.manage_goals'))

@goals_bp.route('/edit/<int:goal_id>', methods=['POST'])
def edit_goal(goal_id):
    goal = models.Goal.query.get_or_404(goal_id)
    goal.name = request.form.get('name')
    goal.target_amount = float(request.form.get('target_amount'))
    target_date_str = request.form.get('target_date')
    goal.target_date = datetime.strptime(target_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc) if target_date_str else None
    
    models.db.session.commit()
    return redirect(url_for('goals.manage_goals'))

@goals_bp.route('/delete/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    goal = models.Goal.query.get_or_404(goal_id)
    
    # Apaga as transações de depósito associadas
    models.Transaction.query.filter(models.Transaction.description.like(f"Depósito para meta: {goal.name}")).delete(synchronize_session=False)
    
    # Apaga a meta
    db.session.delete(goal)
    db.session.commit()
    
    return redirect(url_for('goals.manage_goals'))
