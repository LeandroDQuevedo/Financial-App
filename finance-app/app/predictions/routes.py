# app/predictions/routes.py
from flask import Blueprint, render_template, request, redirect, url_for #type: ignore
from ..core import models

predictions_bp = Blueprint(
    'predictions',
    __name__,
    template_folder='templates'
)

@predictions_bp.route('/predictions', methods=['GET', 'POST'])
def manage_monthly_predictions():
    if request.method == 'POST':
        models.db.session.add(models.RecurringTransaction(
            description=request.form.get('description'),
            amount=float(request.form.get('amount')),
            day_of_month=int(request.form.get('day_of_month')),
            category_id=request.form.get('category_id'),
            type=request.form.get('type')
        ))
        models.db.session.commit()
        return redirect(url_for('predictions.manage_monthly_predictions'))

    predictions = models.RecurringTransaction.query.order_by(models.RecurringTransaction.day_of_month).all()
    return render_template('predictions/predictions.html', predictions=predictions)

@predictions_bp.route('/prediction/edit/<int:prediction_id>', methods=['POST'])
def edit_prediction(prediction_id):
    prediction = models.RecurringTransaction.query.get_or_404(prediction_id)
    prediction.description = request.form.get('description')
    prediction.amount = float(request.form.get('amount'))
    prediction.day_of_month = int(request.form.get('day_of_month'))
    prediction.type = request.form.get('type')
    models.db.session.commit()
    return redirect(url_for('predictions.manage_monthly_predictions'))

@predictions_bp.route('/prediction/delete/<int:prediction_id>', methods=['POST'])
def delete_prediction(prediction_id):
    prediction = models.RecurringTransaction.query.get_or_404(prediction_id)
    models.db.session.delete(prediction)
    models.db.session.commit()
    return redirect(url_for('predictions.manage_monthly_predictions'))