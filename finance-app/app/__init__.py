# app/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    """Cria e configura uma instância da aplicação Flask."""
    app = Flask(__name__)

    # Configurações
    db_path = os.path.join(app.instance_path, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    # O contexto da aplicação é necessário para tudo o que se segue
    with app.app_context():
        # --- NOVO: PROCESSADOR DE CONTEXTO GLOBAL ---
        # Esta função injeta variáveis em todos os templates.
        @app.context_processor
        def inject_common_data():
            """ Injeta dados comuns (categorias, cartões) em todos os templates. """
            from .core.models import Category, CreditCard # Importação local para evitar erros
            all_categories = Category.query.order_by(Category.name).all()
            all_cards = CreditCard.query.order_by(CreditCard.name).all()
            return dict(all_categories=all_categories, all_cards=all_cards)

        # --- REGISTO DOS BLUEPRINTS ---
        from .transactions.routes import transactions_bp
        app.register_blueprint(transactions_bp, url_prefix='/')

        from .goals.routes import goals_bp
        app.register_blueprint(goals_bp, url_prefix='/goals')

        from .budgets.routes import budgets_bp
        app.register_blueprint(budgets_bp, url_prefix='/budgets')

        from .cards.routes import cards_bp
        app.register_blueprint(cards_bp, url_prefix='/cards')

        from .predictions.routes import predictions_bp
        app.register_blueprint(predictions_bp, url_prefix='/predictions')

        from .api.routes import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')

        from .investments.routes import investments_bp
        app.register_blueprint(investments_bp)

        # --- CRIAÇÃO DAS TABELAS ---
        db.create_all()

    return app