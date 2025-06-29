from flask import Flask
from .config import Config
from .routes.chatbot import chatbot_bp
from app.routes.delete_chat import *
from app.routes.audio import *
from app.routes.get_all_conversations import *
from app.routes.new_conversation import *

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    app.register_blueprint(chatbot_bp)
    from app.routes.summary import summary_bp
    app.register_blueprint(summary_bp)
    return app
