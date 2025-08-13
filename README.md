# ForgeGrid
ForgeGrid は、セキュアな認証機能と Markdown 形式でのメモ作成・管理機能を備えた、自己ホスト型のメモアプリケーションです。  
強力な検索機能のために Elasticsearch を統合し、データの永続化には PostgreSQL を使用しています。  
その他、セッション管理にRedisを使用しています。  
また、アクセスにはWebサーバとしてnginxを利用の前提としています。

## 主な機能
- ユーザー認証: 安全なパスワードハッシュ（PBKDF2）と Flask-Login によるセッション管理
- メモ作成・管理: シンプルなインターフェースでメモの作成、編集、削除が可能
- Markdown サポート: メモ本文は Markdown 記法で記述でき、GitHub 風のスタイルでプレビュー表示されます
- 全文検索: Elasticsearch を使用した高速かつ強力な全文検索機能
- 永続化: すべてのメモデータは PostgreSQL に保存されます
- セッション管理: Redis を使用した効率的なセッション管理

## 技術スタック
- バックエンド: Python, Flask, SQLAlchemy
- フロントエンド: Jinja2, Bootstrap 5, Markdown-it
- データベース: PostgreSQL
- 検索エンジン: Elasticsearch
- セッションストア: Redis
- コンテナ: docker, docker-compose

## 利用方法
#### 前提条件
- docker、docker-composeがインストールされていること
- Elasticsearch、及びnginxは自前のものを活用してください
    - Elasticsearchのローカル認証機能を利用するため、ca.crtの発行をしてアプリケーション側がアクセスできるようにしてください
- 起動後、/ForgeGrid/uwsgi.sockが作成されるのでnginxが参照できるようにバインドやボリューム等で共有してください
- docker-composeで立ち上げる前に必ず、docker-compose.ymlのPASS等を修正してください

#### 手順
`git clone https://github.com/MizutoArakawa/ForgeGrid.git`  
`cd ForgeGrid`  
`docker build -t forgegrid:3.2.1 .`  
docker-compose.ymlを修正  
`docker-compose up -d`  
作成されたuwsgi.sockにアクセスできるようにnginxの設定を修正  
nginxにて指定したURLにアクセス

## ディレクトリ構成
```
.
|-- Dockerfile    - コンテナ作成用ファイル
|-- FILE-UPLOAD_DIR    - ファイルアップロード用ディレクトリ
|   `-- 作成したユーザ名
|       `-- ユーザがファイルをアップロードしたもの
|-- README.md
|-- app
|   |-- __init__.py    - アプリケーションが最初に参照するもの
|   |-- certs    - elasticsearch認証用ディレクトリ(独自に変更してもOK)
|   |   `-- ca
|   |       `-- ca.crt
|   |-- config.py    - アプリケーションの設定ファイル
|   |-- forms.py    - ログインやユーザ登録のフォームを定義
|   |-- models.py    - ユーザやノートの情報を定義
|   |-- static    - Flaskを利用しており、cssやjsを呼び出すためのディレクトリ
|   |   |-- css
|   |   |   |-- bootstrap-icons.min.css
|   |   |   |-- bootstrap.min.css
|   |   |   `-- fonts
|   |   |       |-- bootstrap-icons.woff
|   |   |       `-- bootstrap-icons.woff2
|   |   |-- images
|   |   |   |-- ForgeGrid_header.png
|   |   |   |-- ForgeGrid_icon.ico
|   |   |   `-- memo_icon.png
|   |   `-- js
|   |       |-- bootstrap.bundle.min.js
|   |       |-- highlight.min.js
|   |       |-- index.umd.min.js
|   |       `-- marked.min.js
|   |-- templates    - jinja2テンプレート
|   |   |-- base.html    - ベースとなるhtml(主にナビゲーションやフッターのデザイン)
|   |   |-- change_password.html    - パスワード変更画面
|   |   |-- create_note.html    - 新規ノート作成画面
|   |   |-- file_index.html    - ファイルアップロードやダウンロード画面
|   |   |-- home.html    - ログイン後のユーザ画面
|   |   |-- login.html    - ログイン画面
|   |   |-- note.html    - ノート編集画面
|   |   |-- preview.html    - ノート閲覧画面
|   |   `-- register.html    - ユーザ登録画面
|   `-- views.py    - blueprintでの集約をしているapp.routeが記載されたファイル
|-- docker-compose.yml    - docker-compose用ファイル
|-- instance    - postgresql以外にもローカルでデータベースを念のため用意(ユーザを作成してから作成される)
|   `-- new-notes-collection.db
|-- requirements.txt    - コンテナをビルドする際のpipインストールするもの
|-- run.py    - このアプリケーションの根幹
|-- uwsgi.sock    - コンテナを起動すると作成される(これを自前のnginxに共有してください)
`-- uwsgi_ForgeGrid.ini    - uWSGIを起動させるための設定ファイル
```

## アプリケーション イメージ図
#### ログイン画面
<img width="1911" height="903" alt="image" src="https://github.com/user-attachments/assets/65f714da-4c6b-43cd-8a9b-ea1ebb9caf7d" />

#### ログイン後のユーザ画面
<img width="1912" height="899" alt="image" src="https://github.com/user-attachments/assets/3a7f6e1e-28b7-4bdc-8ade-1a4b9851e47b" />

#### ノート プレビュー画面
<img width="1899" height="899" alt="image" src="https://github.com/user-attachments/assets/482f8e62-6e81-4878-9fe1-efe282aece2b" />

#### ノート編集画面
<img width="1896" height="901" alt="image" src="https://github.com/user-attachments/assets/26ad13fc-0da2-41b7-a00e-545acd4d7502" />

#### ファイルアップローダー画面
<img width="1895" height="890" alt="image" src="https://github.com/user-attachments/assets/eaabed33-852e-4936-8b0e-9c393056a2fc" />
