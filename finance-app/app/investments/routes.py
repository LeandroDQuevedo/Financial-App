from flask import Blueprint, render_template, request, redirect, url_for
from app.core import models
from app import db
from . import services
from datetime import datetime

investments_bp = Blueprint(
    'investments',
    __name__,
    template_folder='templates',
    url_prefix='/investments'
)

@investments_bp.route('/', methods=['GET', 'POST'])
def portfolios():
    if request.method == 'POST':
        portfolio_name = request.form.get('name')
        if portfolio_name:
            existing_portfolio = models.Portfolio.query.filter_by(name=portfolio_name).first()
            if not existing_portfolio:
                new_portfolio = models.Portfolio(name=portfolio_name)
                db.session.add(new_portfolio)
                db.session.commit()
    all_portfolios = models.Portfolio.query.all()
    return render_template('investments/portfolios.html', portfolios=all_portfolios)

@investments_bp.route('/<int:portfolio_id>/')
def portfolio_detail(portfolio_id):
    portfolio = models.Portfolio.query.get_or_404(portfolio_id)
    
    # PASSO 1: Chama a função que busca os preços na API
    services.update_variable_asset_prices(portfolio)
    
    # PASSO 2: Calcula o resumo, que agora incluirá o lucro/prejuízo
    summary_data = services.calculate_portfolio_summary(portfolio)
    
    return render_template('investments/portfolio_detail.html', portfolio=portfolio, summary=summary_data)

@investments_bp.route('/portfolio/<int:portfolio_id>/add_variable_asset', methods=['POST'])
def add_variable_asset(portfolio_id):
    ticker = request.form.get('ticker').upper()
    name = request.form.get('name')
    asset_type = request.form.get('asset_type')
    quantity = float(request.form.get('quantity'))
    price = float(request.form.get('price'))

    if ticker and quantity > 0 and price > 0:
        # Verifica se o ativo já existe nesta carteira
        existing_asset = models.VariableAsset.query.filter_by(ticker=ticker, portfolio_id=portfolio_id).first()
        
        # Se já existe, não faz nada (o utilizador deve usar o botão "Comprar")
        if not existing_asset:
            new_asset = models.VariableAsset(
                ticker=ticker,
                name=name,
                asset_type=asset_type,
                quantity=quantity,
                average_price=price, # O preço médio inicial é o preço da primeira compra
                portfolio_id=portfolio_id
            )
            db.session.add(new_asset)
            db.session.commit()
            
    return redirect(url_for('investments.portfolio_detail', portfolio_id=portfolio_id))

@investments_bp.route('/portfolio/<int:portfolio_id>/add_fixed_income_asset', methods=['POST'])
def add_fixed_income_asset(portfolio_id):
    name = request.form.get('name')
    current_amount = float(request.form.get('current_amount')) 
    yield_type = request.form.get('yield_type')
    yield_rate = float(request.form.get('yield_rate'))
    
    maturity_date_str = request.form.get('maturity_date')
    maturity_date = datetime.strptime(maturity_date_str, '%Y-%m-%d') if maturity_date_str else None

    if name and current_amount > 0:
        new_asset = models.FixedIncomeAsset(
            name=name,
            current_amount=current_amount,
            yield_type=yield_type,
            yield_rate=yield_rate,
            maturity_date=maturity_date,
            portfolio_id=portfolio_id
        )
        db.session.add(new_asset)
        db.session.commit()
    return redirect(url_for('investments.portfolio_detail', portfolio_id=portfolio_id))


@investments_bp.route('/variable_asset/<int:asset_id>/transact', methods=['POST'])
def transact_variable_asset(asset_id):
    asset = models.VariableAsset.query.get_or_404(asset_id)
    
    transaction_type = request.form.get('transaction_type')
    quantity = float(request.form.get('quantity'))
    price = float(request.form.get('price'))

    if quantity > 0 and price >= 0:
        services.process_investment_transaction(
            asset_id=asset.id,
            transaction_type=transaction_type,
            quantity=quantity,
            price_per_unit=price
        )
    
    return redirect(url_for('investments.portfolio_detail', portfolio_id=asset.portfolio_id))

@investments_bp.route('/fixed_income/<int:asset_id>/transact', methods=['POST'])
def transact_fixed_income_asset(asset_id):
    asset = models.FixedIncomeAsset.query.get_or_404(asset_id)

    transaction_type = request.form.get('transaction_type')
    amount = float(request.form.get('amount'))

    if amount > 0:
        services.process_fixed_income_transaction(
            asset_id=asset_id,
            transaction_type=transaction_type,
            amount=amount
        )
    return redirect(url_for('investments.portfolio_detail', portfolio_id=asset.portfolio_id))

# --- ROTAS DE EXCLUSÃO ADICIONADAS AQUI ---

@investments_bp.route('/variable_asset/<int:asset_id>/delete', methods=['POST'])
def delete_variable_asset(asset_id):
    asset = models.VariableAsset.query.get_or_404(asset_id)
    portfolio_id = asset.portfolio_id
    
    db.session.delete(asset)
    db.session.commit()
    
    return redirect(url_for('investments.portfolio_detail', portfolio_id=portfolio_id))

@investments_bp.route('/fixed_income_asset/<int:asset_id>/delete', methods=['POST'])
def delete_fixed_income_asset(asset_id):
    asset = models.FixedIncomeAsset.query.get_or_404(asset_id)
    portfolio_id = asset.portfolio_id
    
    db.session.delete(asset)
    db.session.commit()
    
    return redirect(url_for('investments.portfolio_detail', portfolio_id=portfolio_id))