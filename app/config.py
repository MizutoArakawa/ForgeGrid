"""
このファイルはアプリケーションの設定ファイルです。
セッション、データベースファイルの指定、アップロードを許可する拡張子の設定、ElasticSearchの設定
"""

# os: オペレーティングシステムと対話するための機能を提供。ファイルパスの操作、ディレクトリの作成などに使用
import os

# secrets: 暗号学的に強力な乱数を生成するために使用。セッショントークンやパスワードのリセットトークンなど
import secrets

# timedelta: 時間間隔を表現するために使用
from datetime import timedelta

class Config:
    """アプリケーションの設定を管理するクラス"""
    # 秘密鍵: セッション管理やCSRF保護に使用
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

    # SQLAlchemyの設定を環境変数から取得するように変更
    # デフォルトはSQLiteのままにしておくことで、ローカル開発でも動作する
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///new-notes-collection.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # コネクションプールのサイズを設定
    SQLALCHEMY_POOL_SIZE = 10
    # コネクションが使用されていない場合に破棄するまでの秒数
    SQLALCHEMY_POOL_TIMEOUT = 30
    # コネクションが再利用される前にpingテストを行う設定
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True
    }

    # Redisの設定を追加
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    # Redisの接続情報も環境変数から取得
    SESSION_REDIS_URL = f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:6379/0"
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # ファイルアップロードの設定
    UPLOAD_FOLDER = os.path.abspath('./FILE-UPLOAD_DIR')
    # 許可する拡張子
    ALLOWED_EXTENSIONS = {'zip','rdp','ttl','ovf','vmdk','html','txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','csv','docx','pptx','xlsm','xlsx','tar','gz','xls','tiff','bmp','ico','heic','m4v','mov','mp3','m4a','aiff','aifc','wav','m3u','rtf','m3u','rtfd','pub','py','json','jar','dif','doc','docm','iso','msi','pst','db'}

    # Elasticsearchの設定
    ELASTICSEARCH_SCHEME = os.environ.get('ELASTICSEARCH_SCHEME', 'https')
    ELASTICSEARCH_HOST = os.environ.get('ELASTICSEARCH_HOST')
    ELASTICSEARCH_PORT = int(os.environ.get('ELASTICSEARCH_PORT', 9200))
    ELASTICSEARCH_INDEX = 'forgegrid_notes_index'
    ELASTICSEARCH_USER = os.environ.get('ELASTICSEARCH_USER', 'elastic')
    ELASTICSEARCH_PASSWORD = os.environ.get('ELASTICSEARCH_PASSWORD')
    # Dockerコンテナ内のCA証明書のパス
    CA_CERTS_PATH = os.environ.get('ELASTIC_CA_PATH')