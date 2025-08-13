"""
ForgeGridを起動させるためのpyファイル
"""

from app import create_app

# アプリケーションファクトリを呼び出してappインスタンスを作成
app = create_app()

if __name__ == '__main__':
    # アプリケーションを実行
    # host='0.0.0.0' は、外部からのアクセスを許可します (Dockerなどで必要)
    # debug=True にすると、コード変更時に自動でリロードされ、デバッグに便利です
    app.run()