# app/services.py

from .models import db, Transaction, Category, Budget, CreditCard, CardPurchase, Installment, Goal, RecurringTransaction
from sqlalchemy import func # type: ignore
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta # type: ignore

MONTH_NAMES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

def get_unified_feed_for_month(year, month):
    """Busca e unifica todas as transações (à vista, cartão, recorrentes) para um dado mês/ano."""
    unified_feed = []
    
    # Transações à vista (débito e receita)
    cash_transactions = Transaction.query.filter(
        func.extract('year', Transaction.date) == year,
        func.extract('month', Transaction.date) == month
    ).all()
    for tx in cash_transactions:
        aware_date = tx.date.replace(tzinfo=timezone.utc)
        amount = tx.amount if tx.type == 'receita' else -tx.amount
        unified_feed.append({
            'id': tx.id, 'date': aware_date, 'description': tx.description, 
            'category': tx.category.name, 'amount': amount, 'type': 'cash', 
            'is_recurring': False
        })

    # Parcelas de compras no cartão de crédito
    card_installments = Installment.query.join(CardPurchase).filter(
        Installment.invoice_year == year, 
        Installment.invoice_month == month
    ).all()
    for inst in card_installments:
        aware_date = inst.card_purchase.purchase_date.replace(tzinfo=timezone.utc)
        description = f"{inst.card_purchase.description} ({inst.installment_number}/{inst.card_purchase.installments_count})"
        unified_feed.append({
            'id': inst.card_purchase.id, 'date': aware_date, 'description': description,
            'category': inst.card_purchase.category.name, 'amount': -inst.amount,
            'type': 'card', 'card_name': inst.card_purchase.credit_card.name,
            'is_recurring': False
        })

    # Previsões de transações recorrentes
    recurring_transactions = RecurringTransaction.query.all()
    for rt in recurring_transactions:
        try:
            expense_date = datetime(year, month, rt.day_of_month, tzinfo=timezone.utc)
            start_of_week = expense_date - relativedelta(days=3)
            end_of_week = expense_date + relativedelta(days=3)
            
            existing = Transaction.query.filter(
                Transaction.description.ilike(f"%{rt.description}%"),
                Transaction.amount.between(rt.amount * 0.95, rt.amount * 1.05),
                Transaction.date.between(start_of_week, end_of_week)
            ).first()

            if not existing:
                amount = rt.amount if rt.type == 'receita' else -rt.amount
                unified_feed.append({
                    'id': rt.id, 'date': expense_date, 'description': rt.description,
                    'category': rt.category.name, 'amount': amount, 'type': 'recurring',
                    'is_recurring': True
                })
        except ValueError:
            continue
            
    unified_feed.sort(key=lambda x: x['date'], reverse=True)
    return unified_feed

def get_budget_data(year, month):
    """
    Busca os dados de orçamento, incluindo a classe CSS para a barra de progresso.
    """
    budget_data = []
    all_categories = Category.query.all()

    for category in all_categories:
        spent = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.category_id == category.id,
            Transaction.type == 'despesa',
            func.extract('month', Transaction.date) == month,
            func.extract('year', Transaction.date) == year
        ).scalar() or 0.0

        budget_obj = Budget.query.filter_by(category_id=category.id, month=month, year=year).first()
        budget_amount = budget_obj.amount if budget_obj else 0.0

        if budget_amount > 0:
            percentage = (spent / budget_amount * 100)
            
            # LÓGICA DE APRESENTAÇÃO MOVIDA PARA O BACKEND
            progress_class = 'progress-success'
            if percentage > 90:
                progress_class = 'progress-error'
            elif percentage > 70:
                progress_class = 'progress-warning'

            budget_data.append({
                'category_name': category.name,
                'spent': spent,
                'budget': budget_amount,
                'percentage': min(100, percentage),
                'progress_class': progress_class  # A nova variável que será usada no template
            })
    return budget_data

def calculate_monthly_stats(feed):
    """Calcula as receitas, despesas e o saldo com base no feed unificado."""
    total_receita = sum(item['amount'] for item in feed if item['amount'] > 0)
    total_despesa = sum(abs(item['amount']) for item in feed if item['amount'] < 0)
    saldo_mes = total_receita - total_despesa
    return total_receita, total_despesa, saldo_mes

def get_year_options(year):
    """Gera uma lista de anos para os seletores de data."""
    return range(year - 5, year + 6)