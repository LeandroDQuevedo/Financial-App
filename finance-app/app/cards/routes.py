# app/cards/routes.py

from flask import Blueprint, render_template, request, redirect, url_for # type: ignore
from ..core import models, services
from datetime import datetime
from dateutil.relativedelta import relativedelta # type: ignore

# Definimos o novo blueprint 'cards_bp'
cards_bp = Blueprint(
    'cards',
    __name__,
    template_folder='templates'
)

@cards_bp.route('/cards', methods=['GET', 'POST'])
def manage_cards():
    if request.method == 'POST':
        models.db.session.add(models.CreditCard(
            name=request.form.get('name'),
            limit=float(request.form.get('limit')),
            closing_day=int(request.form.get('closing_day')),
            due_day=int(request.form.get('due_day'))
        ))
        models.db.session.commit()
        return redirect(url_for('cards.manage_cards')) # ATUALIZADO
    
    # O template será buscado em 'app/cards/templates/cards/cards.html'
    return render_template('cards/cards.html')

@cards_bp.route('/card/edit/<int:card_id>', methods=['GET', 'POST'])
def edit_card(card_id):
    card = models.CreditCard.query.get_or_404(card_id)
    if request.method == 'POST':
        card.name = request.form.get('name')
        card.limit = float(request.form.get('limit'))
        card.closing_day = int(request.form.get('closing_day'))
        card.due_day = int(request.form.get('due_day'))
        models.db.session.commit()
        return redirect(url_for('cards.manage_cards')) # ATUALIZADO
    
    # O template será buscado em 'app/cards/templates/cards/edit_card.html'
    return render_template('cards/edit_card.html', card=card)

@cards_bp.route('/card/delete/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    card_to_delete = models.CreditCard.query.get_or_404(card_id)
    models.db.session.delete(card_to_delete)
    models.db.session.commit()
    return redirect(url_for('cards.manage_cards')) # ATUALIZADO

@cards_bp.route('/card_invoice/<int:card_id>/<int:year>/<int:month>')
def view_card_invoice(card_id, year, month):
    card = models.CreditCard.query.get_or_404(card_id)
    
    installments = models.Installment.query.join(models.CardPurchase).filter(
        models.CardPurchase.credit_card_id == card_id, 
        models.Installment.invoice_year == year, 
        models.Installment.invoice_month == month
    ).order_by(models.CardPurchase.purchase_date).all()
    
    selected_date = datetime(year, month, 1)
    
    # O template será buscado em 'app/cards/templates/cards/invoice_details.html'
    return render_template(
        'cards/invoice_details.html', 
        card=card, 
        year=year, 
        month=month, 
        installments=installments, 
        total=sum(i.amount for i in installments), 
        selected_month_name=services.MONTH_NAMES[month-1],
        prev_month=selected_date - relativedelta(months=1),
        next_month=selected_date + relativedelta(months=1),
        year_options=services.get_year_options(year)
    )