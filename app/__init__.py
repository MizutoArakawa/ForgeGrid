"""
本アプリケーションの心臓部。
Flaskアプリケーションのインスタンスを作成し、設定を読み込み、各種拡張機能（データベース、ログイン管理など）を初期化する「アプリケーションファクトリ」というパターン
"""

# os: オペレーティングシステムと対話するための機能を提供。ファイルパスの操作、ディレクトリの作成などに使用
import os

# Flask: ウェブアプリケーションの主要なフレームワーク
from flask import Flask

# Bootstrap: FlaskアプリケーションでBootstrapフレームワークを使用するための拡張機能。CSSとJavaScriptを簡単に統合
from flask_bootstrap import Bootstrap

# LoginManager: Flaskアプリケーションのログインプロセスを管理
from flask_login import LoginManager

# Admin: Flaskアプリケーションに管理インターフェースを追加するための拡張機能。データベースモデルの管理などが可能
from flask_admin import Admin

# ModelView: Flask-AdminでSQLAlchemyモデルを管理するためのビューを提供
from flask_admin.contrib.sqla import ModelView

# elasticsearch用
from elasticsearch import Elasticsearch

# markdown: MarkdownテキストをHTMLに変換するために使用。メモ帳アプリの主要な機能の一部(本アプリのメイン)
import markdown

# Markup: HTML文字列を「安全」としてマークするために使用。これにより、Jinja2テンプレートでエスケープされずに表示
from markupsafe import Markup

# pymdownx.tasklist: Markdownでタスクリスト（チェックボックス付きリスト）をサポートするための拡張機能
from pymdownx.tasklist import TasklistExtension

# markdown.extensions.fenced_code: Markdownでフェンス付きコードブロック（```python ... ```）をサポートするための拡張機能
# markdown.extensions.tables: Markdownでテーブル（表）をサポートするための拡張機能
# markdown.extensions.nl2br: Markdownで改行（new line）を `<br>` タグに変換するための拡張機能
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.nl2br import Nl2BrExtension

# models.pyからdbオブジェクトとモデルクラスをインポート
from .models import db, User, Note
# config.pyからConfigクラスをインポート
from .config import Config

# redisでセッション管理するために
from flask_session import Session
from redis import Redis


# 各拡張機能のインスタンスを生成
bootstrap = Bootstrap()
login_manager = LoginManager()
admin = Admin(name='ForgeGrid Admin', template_mode='bootstrap3')
es = None # グローバル変数としてesを定義
sess = Session()

def create_app():
    """アプリケーションインスタンスを作成するファクトリ関数"""
    global es
    
    app = Flask(__name__)
    
    # 設定クラスを読み込み
    app.config.from_object(Config)

    # Flask-Sessionを初期化
    app.config["SESSION_REDIS"] = Redis.from_url(app.config["SESSION_REDIS_URL"])
    sess.init_app(app)

    # 各拡張機能をアプリケーションに初期化(紐付け)
    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app)

    # Elasticsearchクライアントの初期化
    es = Elasticsearch(
        hosts=[{'host': app.config['ELASTICSEARCH_HOST'], 'port': app.config['ELASTICSEARCH_PORT'], 'scheme': app.config['ELASTICSEARCH_SCHEME']}],
        ca_certs=app.config['CA_CERTS_PATH'],
        basic_auth=(app.config['ELASTICSEARCH_USER'], app.config['ELASTICSEARCH_PASSWORD']),
    )

    # ログインしていない場合にリダイレクトするページを設定
    login_manager.login_view = 'views.login'

    # Flask-Loginのuser_loaderコールバック関数
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # 管理画面にモデルを追加
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Note, db.session))

    # Markdown変換フィルターを登録
    @app.template_filter('markdown_to_html')
    def markdown_to_html(text):
        html = markdown.markdown(text, extensions=[
            FencedCodeExtension(),
            TableExtension(),
            'nl2br',
            TasklistExtension(),
            'codehilite',
        ])
        return Markup(html)

    # views.pyで定義したルート(Blueprint)を登録
    from . import views
    app.register_blueprint(views.bp, url_prefix='/')

    with app.app_context():
        # データベーステーブルを作成
        db.create_all()
        
        # Elasticsearchのインデックスを作成
        es_index_name = app.config['ELASTICSEARCH_INDEX']
        if es and not es.indices.exists(index=es_index_name):
            try:
                # マッピングを定義
                mapping = {
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "text"},
                        "content": {"type": "text"},
                        "date": {"type": "date"},
                        "user_id": {"type": "integer"}
                    }
                }
                # インデックス作成時にマッピングを適用
                es.indices.create(index=es_index_name, body={"mappings": mapping})
                print(f"Elasticsearch index '{es_index_name}' created.")
            except Exception as e:
                print(f"Error creating Elasticsearch index: {e}")

    return app