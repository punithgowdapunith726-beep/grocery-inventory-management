from pathlib import Path
from flask import Flask
from config import Config
from .extensions import db, login_manager, migrate, csrf


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    db.init_app(app); login_manager.init_app(app); migrate.init_app(app, db); csrf.init_app(app)
    login_manager.login_view = "auth.login"; login_manager.login_message_category = "warning"
    from .models import User
    @login_manager.user_loader
    def load_user(user_id): return db.session.get(User, int(user_id))
    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    app.register_blueprint(auth_bp); app.register_blueprint(main_bp)
    @app.errorhandler(403)
    def forbidden(_error):
        from flask import render_template
        return render_template("403.html"), 403
    from .seed import seed_command
    app.cli.add_command(seed_command)
    @app.context_processor
    def helpers():
        from datetime import date
        return {"today": date.today()}
    return app
