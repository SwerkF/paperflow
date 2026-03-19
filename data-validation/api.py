from flask import Flask
from documents import documents_bp

def create_app():
    app = Flask(__name__)

    app.config["JSON_AS_ASCII"] = False
    try:
        app.json.ensure_ascii = False
    except Exception:
        pass

    app.register_blueprint(documents_bp)

    @app.route('/', methods=['GET'])
    def health_check():
        return {"statut": "API de Validation HKT 2026 opérationnelle."}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5030)