# app/investments/services.py

from app.core import models
from app import db
import yfinance as yf
from datetime import datetime, timezone, timedelta
from itertools import groupby
from collections import defaultdict

def process_investment_transaction(asset_id, transaction_type, quantity, price_per_unit):
    """Processa e AGORA GUARDA o histórico de uma transação de Ativo Variável."""
    asset = models.VariableAsset.query.get(asset_id)
    if not asset:
        return

    # 1. Cria e guarda o registo histórico da transação
    new_transaction = models.VariableAssetTransaction(
        asset_id=asset_id,
        transaction_type=transaction_type,
        quantity=quantity,
        price_per_unit=price_per_unit
    )
    db.session.add(new_transaction)
    
    # 2. Atualiza o estado atual do ativo
    if transaction_type == 'buy':
        total_cost_of_existing_shares = asset.average_price * asset.quantity
        total_cost_of_new_shares = price_per_unit * quantity
        new_total_quantity = asset.quantity + quantity
        if new_total_quantity > 0:
            asset.average_price = (total_cost_of_existing_shares + total_cost_of_new_shares) / new_total_quantity
        asset.quantity = new_total_quantity
    elif transaction_type == 'sell':
        asset.quantity = max(0, asset.quantity - quantity)
        if asset.quantity == 0:
            asset.average_price = 0

    db.session.commit()

def process_fixed_income_transaction(asset_id, transaction_type, amount):
    """
    Processa um aporte ou resgate num ativo de Renda Fixa.
    """
    asset = models.FixedIncomeAsset.query.get(asset_id)
    if not asset:
        return

    # 1. Cria o registo da transação
    new_transaction = models.FixedIncomeTransaction(
        asset_id=asset_id,
        transaction_type=transaction_type,
        amount=amount
    )
    db.session.add(new_transaction)

    # 2. Atualiza o valor total do ativo
    if transaction_type == 'aporte':
        asset.current_amount += amount
    elif transaction_type == 'resgate':
        asset.current_amount = max(0, asset.current_amount - amount)

    # 3. Salva as alterações
    db.session.commit()

def calculate_portfolio_summary(portfolio):
    """Calcula os dados de resumo para o dashboard da carteira."""
    
    # --- 1. Cálculos para os cartões e Gráfico de Alocação por Ativo ---
    
    total_invested = 0
    total_market_value = 0

    all_assets_summary = []

    for asset in portfolio.variable_assets:
        cost = asset.quantity * asset.average_price
        all_assets_summary.append({'name': asset.ticker, 'cost': cost})
        total_invested += cost
        
    for asset in portfolio.fixed_income_assets:
        all_assets_summary.append({'name': asset.name, 'cost': asset.current_amount})
        total_invested += asset.current_amount

    # Ordena os ativos por valor para o gráfico
    all_assets_summary.sort(key=lambda x: x['cost'], reverse=True)
    
    # --- 2. Cálculos para o Gráfico de Crescimento do Capital ---
    all_transactions = []
    for asset in portfolio.variable_assets:
        cost = asset.quantity * asset.average_price
        market_value = asset.quantity * (asset.current_price or 0)
        total_invested += cost
        total_market_value += market_value
        
    for asset in portfolio.fixed_income_assets:
        total_invested += asset.current_amount
        total_market_value += asset.current_amount # Por enquanto, o valor de mercado da RF é o valor atual

    # Lucro / Prejuízo Total
    total_pnl = total_market_value - total_invested
    
    all_transactions.sort(key=lambda x: x['date'])
    
    growth_data = defaultdict(float)
    for date, group in groupby(all_transactions, key=lambda x: x['date'].strftime('%Y-%m')):
        growth_data[date] = sum(tx['amount'] for tx in group)
    
    cumulative_growth = 0
    cumulative_data = {}
    for date in sorted(growth_data.keys()):
        cumulative_growth += growth_data[date]
        cumulative_data[date] = round(cumulative_growth, 2)

    summary = {
        'total_invested': total_invested,
        'total_market_value': total_market_value,
        'total_pnl': total_pnl,
        'asset_allocation': {
            'labels': [item['name'] for item in all_assets_summary],
            'data': [item['cost'] for item in all_assets_summary]
        },
        'capital_growth': {
            'labels': list(cumulative_data.keys()),
            'data': list(cumulative_data.values())
        }
    }
    return summary

def update_variable_asset_prices(portfolio):
    """Busca os preços atuais para os ativos de renda variável de uma carteira."""
    for asset in portfolio.variable_assets:
        # Só busca o preço se não tiver sido atualizado nos últimos 15 minutos
        now_naive_utc = datetime.utcnow()
        needs_update = not asset.last_updated or (now_naive_utc - asset.last_updated > timedelta(minutes=15))
        
        if needs_update and asset.quantity > 0:
            try:
                # Para ações brasileiras, o yfinance espera o sufixo '.SA'
                ticker_symbol = asset.ticker if '.' in asset.ticker else f"{asset.ticker}.SA"
                
                # Criptomoedas geralmente são no formato 'BTC-USD'
                if asset.asset_type == 'Criptomoeda':
                     # Adapte conforme necessário, ex: 'ETH-USD'
                    ticker_symbol = f"{asset.ticker}-USD"

                ticker = yf.Ticker(ticker_symbol)
                history = ticker.history(period='1d')
                
                if not history.empty:
                    last_price = history['Close'].iloc[-1]
                    asset.current_price = last_price
                    asset.last_updated = datetime.now(timezone.utc)
            except Exception as e:
                print(f"Erro ao buscar preço para {asset.ticker}: {e}")
    db.session.commit()