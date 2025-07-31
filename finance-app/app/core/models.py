# app/core/models.py

from .. import db
from datetime import datetime, timezone

# --- Modelos Principais ---

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('transactions', lazy=True))

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('month', 'year', 'category_id', name='_month_year_category_uc'),)

class CreditCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    limit = db.Column(db.Float, nullable=False, default=0.0)
    closing_day = db.Column(db.Integer, nullable=False)
    due_day = db.Column(db.Integer, nullable=False)
    purchases = db.relationship('CardPurchase', backref='credit_card', lazy=True, cascade="all, delete-orphan")

class CardPurchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    installments_count = db.Column(db.Integer, nullable=False, default=1)
    purchase_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    credit_card_id = db.Column(db.Integer, db.ForeignKey('credit_card.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('card_purchases', lazy=True))
    installments = db.relationship('Installment', backref='card_purchase', lazy=True, cascade="all, delete-orphan")

class Installment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    installment_number = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    invoice_month = db.Column(db.Integer, nullable=False)
    invoice_year = db.Column(db.Integer, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    card_purchase_id = db.Column(db.Integer, db.ForeignKey('card_purchase.id'), nullable=False)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, nullable=False, default=0.0)
    target_date = db.Column(db.DateTime, nullable=True)
    creation_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    @property
    def progress_percent(self):
        if not self.target_amount or self.target_amount == 0:
            return 0.0
        return min(100.0, (self.current_amount / self.target_amount) * 100)

class RecurringTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    day_of_month = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('recurring_transactions', lazy=True))

    @property
    def display_amount(self):
        return f"+ R$ {self.amount:.2f}" if self.type == 'receita' else f"- R$ {self.amount:.2f}"

# --- Modelos de Investimento ---

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    variable_assets = db.relationship('VariableAsset', backref='portfolio', lazy=True, cascade="all, delete-orphan")
    fixed_income_assets = db.relationship('FixedIncomeAsset', backref='portfolio', lazy=True, cascade="all, delete-orphan")

class VariableAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    asset_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0.0)
    average_price = db.Column(db.Float, nullable=False, default=0.0)
    creation_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    transactions = db.relationship('VariableAssetTransaction', backref='asset', lazy=True, cascade="all, delete-orphan")
    current_price = db.Column(db.Float, nullable=True, default=0.0)
    last_updated = db.Column(db.DateTime, nullable=True)

class FixedIncomeAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    current_amount = db.Column(db.Float, nullable=False) 
    investment_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    yield_type = db.Column(db.String(50), nullable=False)
    yield_rate = db.Column(db.Float, nullable=False)
    maturity_date = db.Column(db.DateTime, nullable=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    transactions = db.relationship('FixedIncomeTransaction', backref='asset', lazy=True, cascade="all, delete-orphan")

class FixedIncomeTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    asset_id = db.Column(db.Integer, db.ForeignKey('fixed_income_asset.id'), nullable=False)

class VariableAssetTransaction(db.Model):
    """Regista uma operação de compra ou venda de um Ativo Variável."""
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(10), nullable=False) # 'buy' ou 'sell'
    quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    asset_id = db.Column(db.Integer, db.ForeignKey('variable_asset.id'), nullable=False)