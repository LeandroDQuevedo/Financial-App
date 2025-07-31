from flask import Blueprint, render_template, request, redirect, url_for # type: ignore
from ..core import services, models
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta # type: ignore

# Define o Blueprint para este módulo
transactions_bp = Blueprint(
    'transactions', 
    __name__,
    template_folder='templates'
)

# A rota principal agora pertence a este blueprint
@transactions_bp.route('/')
def index():
    now = datetime.now(timezone.utc)
    return redirect(url_for('transactions.dashboard', year=now.year, month=now.month))

@transactions_bp.route('/dashboard/<int:year>/<int:month>')
def dashboard(year, month):
    # Garante que categorias padrão existam
    if models.Category.query.count() == 0:
        default_categories = ['Alimentação', 'Transporte', 'Moradia', 'Lazer', 'Salário', 'Outros', 'Metas']
        for cat_name in default_categories:
            if not models.Category.query.filter_by(name=cat_name).first():
                models.db.session.add(models.Category(name=cat_name))
        models.db.session.commit()

    selected_date = datetime(year, month, 1)
    
    unified_feed = services.get_unified_feed_for_month(year, month)
    budget_data = services.get_budget_data(year, month)
    total_receita, total_despesa, saldo_mes = services.calculate_monthly_stats(unified_feed)

    # O template 'transactions/index.html' será procurado na pasta de templates deste blueprint
    return render_template('transactions/index.html',
                           feed=unified_feed, 
                           budget_data=budget_data,
                           total_receita_mes=total_receita, 
                           total_despesa_mes=total_despesa, 
                           saldo_mes=saldo_mes,
                           selected_year=year, 
                           selected_month=month, 
                           selected_month_name=services.MONTH_NAMES[month-1],
                           prev_month=selected_date - relativedelta(months=1),
                           next_month=selected_date + relativedelta(months=1),
                           year_options=services.get_year_options(year))

@transactions_bp.route('/transaction/add', methods=['POST'])
def add_transaction():
    payment_method = request.form.get('payment_method')
    description = request.form.get('description')
    amount = float(request.form.get('amount', '0').replace(',', '.'))
    category_id = request.form.get('category_id')

    if payment_method == 'cash_debit':
        tx_type = 'receita' if amount > 0 else 'despesa'
        models.db.session.add(models.Transaction(description=description, amount=abs(amount), type=tx_type, category_id=category_id, date=datetime.now(timezone.utc)))
    
    elif payment_method.startswith('card_'):
        card_id = int(payment_method.split('_')[1])
        installments_count = int(request.form.get('installments', 1))
        card = models.CreditCard.query.get_or_404(card_id)
        purchase_date = datetime.now(timezone.utc)
        
        new_purchase = models.CardPurchase(description=description, total_amount=amount, installments_count=installments_count, purchase_date=purchase_date, credit_card_id=card_id, category_id=category_id)
        models.db.session.add(new_purchase)
        
        installment_amount = round(amount / installments_count, 2)
        for i in range(installments_count):
            invoice_date = purchase_date
            if purchase_date.day >= card.closing_day:
                invoice_date += relativedelta(months=1)
            invoice_date += relativedelta(months=i)
            models.db.session.add(models.Installment(card_purchase=new_purchase, installment_number=i + 1, amount=installment_amount, invoice_month=invoice_date.month, invoice_year=invoice_date.year))

    models.db.session.commit()
    return redirect(request.referrer or url_for('transactions.index'))

@transactions_bp.route('/transaction/edit/<string:tx_type>/<int:tx_id>', methods=['GET', 'POST'])
def edit_transaction(tx_type, tx_id):
    transaction_obj = None
    if tx_type == 'cash':
        transaction_obj = models.Transaction.query.get_or_404(tx_id)
    elif tx_type == 'card':
        transaction_obj = models.CardPurchase.query.get_or_404(tx_id)
    
    tx_date = transaction_obj.date if tx_type == 'cash' else transaction_obj.purchase_date

    if request.method == 'POST':
        transaction_obj.description = request.form.get('description')
        transaction_obj.category_id = request.form.get('category_id')
        amount = float(request.form.get('amount').replace(',', '.'))
        
        if tx_type == 'cash':
            transaction_obj.amount = abs(amount)
            transaction_obj.type = 'receita' if amount >= 0 else 'despesa'
        
        elif tx_type == 'card':
            models.Installment.query.filter_by(card_purchase_id=tx_id).delete()
            transaction_obj.total_amount = amount
            transaction_obj.installments_count = int(request.form.get('installments'))
            transaction_obj.credit_card_id = request.form.get('credit_card_id')
            card = models.CreditCard.query.get(transaction_obj.credit_card_id)
            
            installment_amount = round(amount / transaction_obj.installments_count, 2)
            for i in range(transaction_obj.installments_count):
                invoice_date = transaction_obj.purchase_date
                if transaction_obj.purchase_date.day >= card.closing_day:
                    invoice_date += relativedelta(months=1)
                invoice_date += relativedelta(months=i)
                models.db.session.add(models.Installment(card_purchase=transaction_obj, installment_number=i+1, amount=installment_amount, invoice_month=invoice_date.month, invoice_year=invoice_date.year))

        models.db.session.commit()
        return redirect(url_for('transactions.dashboard', year=tx_date.year, month=tx_date.month))
    
    # O template 'transactions/edit_transaction.html' será renderizado a partir daqui
    return render_template('transactions/edit_transaction.html', transaction=transaction_obj, tx_type=tx_type, tx_date=tx_date)

@transactions_bp.route('/transaction/delete/<string:tx_type>/<int:tx_id>', methods=['POST'])
def delete_transaction(tx_type, tx_id):
    if tx_type == 'cash':
        tx_to_delete = models.Transaction.query.get_or_404(tx_id)
        tx_date = tx_to_delete.date
        models.db.session.delete(tx_to_delete)
    elif tx_type == 'card':
        purchase_to_delete = models.CardPurchase.query.get_or_404(tx_id)
        tx_date = purchase_to_delete.purchase_date
        models.db.session.delete(purchase_to_delete)
    
    models.db.session.commit()
    return redirect(url_for('transactions.dashboard', year=tx_date.year, month=tx_date.month))