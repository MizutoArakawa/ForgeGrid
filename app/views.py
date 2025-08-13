"""
URLへのアクセスとそれに対応する処理（関数）を定義する部分です。
@app.route() の部分をすべてこちらに集めます。Blueprint という機能を使って、ルート定義をグループ化します。
"""

# os: オペレーティングシステムと対話するための機能を提供。ファイルパスの操作、ディレクトリの作成などに使用
import os

# base64: バイナリデータをASCII文字列にエンコード/デコードするために使用。ファイルの埋め込みなどに使われる(本アプリでは画像のペーストで取り扱う)
import base64

# uuid: Universally Unique Identifier（普遍的識別子）を生成するために使用
# 一意なファイル名やIDの生成(本アプリではスクリーンショットをペーストした際に自動保存される際に生成)
import uuid

# humanize: 数値や日付を人間が読みやすい形式に変換するために使用（例：1000000を"1 million"に）
import humanize

# timedelta: 時間間隔を表現するために使用
# datetime: 日付と時刻を扱うために使用
# timezone: タイムゾーン情報を扱うために使用
# date: 日付のみを扱うために使用
from datetime import date, datetime, timedelta, timezone

# secure_filename: アップロードされたファイル名を安全にするために使用し、ファイル名に含まれる可能性のある悪意のある文字を除去
from werkzeug.utils import secure_filename

# generate_password_hash: パスワードをハッシュ化するために使用
# check_password_hash: ハッシュ化されたパスワードと入力されたパスワードが一致するかどうかを確認するために使用
from werkzeug.security import generate_password_hash, check_password_hash

# elasticsearch用 エラー処理
from elasticsearch import NotFoundError

# render_template: 指定されたJinja2テンプレートをレンダリングするために使用することでHTMLファイルを動的に生成
# request: クライアントからのHTTPリクエストに関するデータ（フォームデータ、ファイルなど）を扱うために使用
# redirect: ユーザーを別のURLにリダイレクトするために使用
# url_for: 指定された関数にURLを生成するために使用し、URLのハードコーディングを防ぎ、保守性を高める
# flash: ユーザーにメッセージ（例：成功メッセージ、エラーメッセージ）を一時的に表示するために使用
# send_from_directory: 指定されたディレクトリからファイルを送信するために使用し、ファイルダウンロード機能などに使われる
# session: ユーザー固有のデータをサーバー側で一時的に保存するために使用。ログイン状態の保持したいため
# jsonify: Python辞書をJSON形式のレスポンスに変換するために使用。APIエンドポイント
# make_response: HTTPレスポンスを明示的に作成するために使用。カスタムヘッダーの設定などで使用
# get_flashed_messages: flashで設定されたメッセージを取得するため
# Blueprint: ルート定義をグループ化
from flask import (
    render_template, request, redirect, url_for, flash, send_from_directory,
    session, jsonify, make_response, Blueprint, current_app
)

# login_user: ユーザーをログイン状態にするために使用
# login_required: 特定のルートにアクセスするためにログインが必要であることを示すデコレータ
# current_user: 現在ログインしているユーザーのオブジェクトにアクセスするために使用
# logout_user: 現在のユーザーをログアウトするために使用
from flask_login import login_user, login_required, current_user, logout_user

# __init__.pyで初期化されたesと、models.pyのdbとモデルをインポート
from . import es
from .models import db, User, Note
from .forms import LoginForm, RegisterForm

# Blueprintを作成
bp = Blueprint('views', __name__,
               url_prefix='/ForgeGrid',
               static_folder='static',
               static_url_path='/ForgeGrid/static')

def allwed_file(filename):
    """許可された拡張子かチェック"""
    from flask import current_app
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def sync_note_to_elasticsearch(note):
    """メモをElasticsearchに同期するヘルパー関数"""
    try:
        es.index(index=current_app.config['ELASTICSEARCH_INDEX'], id=note.id, document={
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'date': note.date.isoformat() if isinstance(note.date, date) else note.date, # 日付形式を適切に処理
            'user_id': note.user_id
        })
        return True, "ノートがElasticsearchに同期されました。"
    except Exception as e:
        current_app.logger.error(f"Elasticsearch synchronization error: {e}")
        return False, f"ノートの更新はできましたが、Elasticsearch同期中にエラーが発生しました: {e}"


# @bp.before_app_request
# def before_request():
#     """リクエストの前にセッションを永続化し、Cookieで自動ログイン"""
#     session.permanent = True
#     if 'user_id' in request.cookies and not current_user.is_authenticated:
#         user = db.session.get(User, request.cookies.get('user_id'))
#         if user:
#             login_user(user)

# アイコン設定
@bp.route('/ForgeGrid/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(bp.root_path, 'static/images'), 'ForgeGrid_icon.ico')

# --- ログイン・登録関連 ---
@bp.route('/ForgeGrid/login', methods=['GET', 'POST'])
def login():
    """ユーザーログインを処理するルート"""
    # ユーザーが既にログインしているかを確認
    if current_user.is_authenticated:
        # ログイン済みであれば、ホーム画面にリダイレクト
        flash("ログイン済み", "info")
        return redirect(url_for('views.home'))

    login_form = LoginForm()
    if login_form.validate_on_submit():
        user_result = db.session.execute(db.select(User).where(User.username == login_form.username.data)).scalar()
        if user_result and check_password_hash(user_result.password, login_form.password.data):
            login_user(user_result)
            # current_app.permanent_session_lifetime = timedelta(weeks=48)
            # response = make_response(redirect(url_for('views.home')))
            # response.set_cookie('user_id', str(user_result.id), max_age=timedelta(days=365), httponly=True, samesite='Lax')
            flash(f"ようこそ、{user_result.username}さん！", "success")
            return redirect(url_for('views.home'))
        else:
            flash("ユーザー名またはパスワードが正しくありません。", "danger")
    return render_template("login.html", form=login_form)

@bp.route('/ForgeGrid/register', methods=['GET', 'POST'])
def register():
    """ユーザー登録を処理するルート"""
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        user_result = db.session.execute(db.select(User).where(User.username == register_form.username.data)).scalar()
        if user_result:
            flash("既にユーザー登録されています。", "warning")
            return render_template("register.html", form=register_form)
        with current_app.app_context():
            new_user = User(
                username=register_form.username.data,
                password=generate_password_hash(register_form.password.data, method="pbkdf2", salt_length=8),
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            user_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], new_user.username)
            os.makedirs(user_upload_folder, exist_ok=True)
        flash("ユーザー登録が完了しました。", "success")
        return redirect(url_for('views.home'))
    return render_template("register.html", form=register_form)

@bp.route("/ForgeGrid/logout", methods=["GET"])
@login_required
def logout():
    """ユーザーをログアウトさせるルート"""
    logout_user()
    # response = make_response(redirect(url_for("views.login")))
    # response.delete_cookie('user_id')
    # Flask-Sessionがセッションを管理するため、クッキーを手動で削除する必要はありません。
    flash("ログアウトしました。", "success")
    return redirect(url_for("views.login"))

# --- メモ管理関連 ---
@bp.route('/ForgeGrid')
@login_required
def home():
    """アプリケーションのホームページを処理するルート"""
    user_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.username)
    os.makedirs(user_upload_folder, exist_ok=True)
    
    SearchText = request.args.get('search', '').strip()
    notes_result = []

    # 検索クエリがない場合は常にPostgreSQLからデータを取得
    notes_result = db.session.execute(
        db.select(Note)
        .where(Note.user_id == current_user.id)
        .order_by(Note.id.desc())
    ).scalars().all()

    # コンテンツプレビューの生成
    for note in notes_result:
        note.content_preview = (note.content[:75] + "...") if len(note.content) > 75 else note.content

    if SearchText:
        # 検索クエリがある場合のみElasticsearchを使用
        try:
            search_body = {
                "query": {
                    "bool": {
                        "must": [{"term": {"user_id": current_user.id}}],
                        "should": [
                            {"match": {"title": {"query": SearchText, "fuzziness": "AUTO"}}},
                            {"match": {"content": {"query": SearchText, "fuzziness": "AUTO"}}}
                        ],
                        "minimum_should_match": 1
                    }
                },
                "sort": [{"date": {"order": "desc"}}]
            }
            res = es.search(index=current_app.config['ELASTICSEARCH_INDEX'], body=search_body)
            # Elasticsearchの結果は辞書形式なので、ORMオブジェクトに変換する
            note_ids = [hit['_source']['id'] for hit in res['hits']['hits']]
            if note_ids:
                notes_result = db.session.execute(db.select(Note).where(Note.id.in_(note_ids)).order_by(Note.id.desc())).scalars().all()
            
        except Exception as e:
            flash(f"検索中にエラーが発生しました: {e}", "danger")

    return render_template('home.html', note_data=notes_result, logged_in=current_user.is_authenticated, logged_user=current_user.username)


@bp.route('/ForgeGrid/search_notes_async', methods=['POST'])
@login_required
def search_notes_async():
    """非同期でのメモ検索を処理するルート"""
    if not es:
        return jsonify({'error': 'Elasticsearchサービスが利用できません。'}), 503
    try:
        search_term = request.form.get('search', '').strip()
        
        if search_term:
            query_body = {
                "query": {
                    "bool": {
                        "filter": [{"term": {"user_id": current_user.id}}],
                        "should": [
                            {"match": {"title": {"query": search_term, "fuzziness": "AUTO"}}},
                            {"match": {"content": {"query": search_term, "fuzziness": "AUTO"}}}
                        ],
                        "minimum_should_match": 1
                    }
                },
                "sort": [{"date": {"order": "desc"}}]
            }
        else:
            query_body = {
                "query": {"term": {"user_id": current_user.id}},
                "sort": [{"date": {"order": "desc"}}]
            }
        
        res = es.search(index=current_app.config['ELASTICSEARCH_INDEX'], body=query_body)
        notes_data = []
        for hit in res['hits']['hits']:
            source = hit['_source']
            notes_data.append({
                'id': source['id'],
                'title': source['title'],
                'content_preview': (source['content'][:75] + '...') if len(source['content']) > 75 else source['content'],
                'date': source['date']
            })
        return jsonify(notes_data)
    except Exception as e:
        current_app.logger.error(f"Elasticsearch search error: {e}")
        return jsonify({'error': f'検索中にエラーが発生しました: {e}'}), 500

@bp.route("/ForgeGrid/note_edit/<int:note_id>", methods=["GET", "POST"])
@login_required
def note_edit(note_id):
    """既存のメモを編集するためのルート"""
    note_result = db.session.get(Note, note_id)
    if not note_result or note_result.user_id != current_user.id:
        flash("ノートが見つからないか、アクセス権がありません。", "danger")
        return redirect(url_for('views.home'))
    if request.method == 'GET':
        return render_template('note.html', note_data=note_result)
    else:
        note_result.title = request.form['title']
        note_result.content = request.form['content']
        db.session.commit()
        success, message = sync_note_to_elasticsearch(note_result)
        flash(message, "success" if success else "danger")
        return render_template('preview.html', note_data=note_result)

@bp.route("/ForgeGrid/preview/<int:note_id>", methods=["GET", "POST"])
@login_required
def preview(note_id):
    """メモのプレビュー表示を処理するルート"""
    note_result = db.session.get(Note, note_id)
    if not note_result or note_result.user_id != current_user.id:
        flash("ノートが見つからないか、アクセス権がありません。", "danger")
        return redirect(url_for('views.home'))
    if request.method == 'GET':
        return render_template('preview.html', note_data=note_result)
    else:
        note_result.title = request.form['title']
        note_result.content = request.form['content']
        db.session.commit()
        success, message = sync_note_to_elasticsearch(note_result)
        flash(message, "success" if success else "danger")
        return redirect(url_for('views.home'))

@bp.route("/ForgeGrid/note_create", methods=["GET", "POST"])
@login_required
def note_create():
    """新しいメモを作成するためのルート"""
    if request.method == 'GET':
        return render_template('create_note.html', note_data=None)
    else:
        with current_app.app_context():
            new_note = Note(
                title=request.form['title'],
                content=request.form['content'],
                date=date.today(), # dateオブジェクトとして保存
                user=current_user)
            db.session.add(new_note)
            db.session.commit()
            success, message = sync_note_to_elasticsearch(new_note)
            flash(message, "success" if success else "danger")
        return redirect(url_for('views.home'))

@bp.route("/ForgeGrid/note_delete/<int:note_id>", methods=["GET", "POST"])
@login_required
def note_delete(note_id):
    """メモを削除するためのルート"""
    note_to_delete = db.session.get(Note, note_id)
    if not note_to_delete or note_to_delete.user_id != current_user.id:
        flash("ノートが見つからないか、削除する権限がありません。", "danger")
        return redirect(url_for('views.home'))

    db.session.delete(note_to_delete)
    db.session.commit()
    try:
        es.delete(index=current_app.config['ELASTICSEARCH_INDEX'], id=note_id)
        flash("ノートが削除され、Elasticsearchからも削除されました。", "success")
    except NotFoundError:
        flash("ノートは削除されましたが、Elasticsearchから見つかりませんでした。", "warning")
    except Exception as e:
        flash(f"ノートの削除はできましたが、Elasticsearchからの削除中にエラーが発生しました: {e}", "danger")
    return redirect(url_for('views.home'))

# --- ファイル操作関連 ---
@bp.route('/ForgeGrid/file_upload')
@login_required
def file_upload():
    """ファイルアップロード機能の操作画面を表示するルート"""
    user_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.username)
    os.makedirs(user_upload_folder, exist_ok=True)
    
    directory_files = []
    for file in os.listdir(user_upload_folder):
        file_path = os.path.join(user_upload_folder, file)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            directory_files.append({
                'filename': file,
                'size': humanize.naturalsize(stat.st_size),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y年%m月%d日 %H:%M:%S')
            })
    return render_template('file_index.html', directory_files=directory_files)

@bp.route('/ForgeGrid/upload_file', methods=["POST"])
def upload():
    """ファイルのアップロードを処理するルート"""
    file = request.files.get('file')
    if not file or file.filename == '' or not allwed_file(file.filename):
        flash('無効なファイルがアップロードされました。', 'danger')
        return redirect(url_for('views.file_upload'))
    
    filename = secure_filename(file.filename)
    user_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.username)
    save_path = os.path.join(user_upload_folder, datetime.now().strftime("%Y%m%d_%H%M%S_") + filename)
    file.save(save_path)
    flash("ファイルがアップロードされました。", "success")
    return redirect(url_for('views.file_upload'))

@bp.route('/ForgeGrid/download/<string:file>')
@login_required
def download(file):
    """ファイルのダウンロードを処理するルート"""
    user_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.username)
    return send_from_directory(user_upload_folder, file, as_attachment=True)

@bp.route('/ForgeGrid/delete/<string:file>')
@login_required
def delete(file):
    """ファイルを削除するルート"""
    user_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.username)
    delete_file_path = os.path.join(user_upload_folder, secure_filename(file))
    if os.path.exists(delete_file_path) and os.path.isfile(delete_file_path):
        os.remove(delete_file_path)
        flash("ファイルが削除されました。", "success")
    else:
        flash("ファイルが見つかりません。", "danger")
    return redirect(url_for('views.file_upload'))

@bp.route('/ForgeGrid/<filename>')
@login_required
def Markdown_imagefile(filename):
    """Markdown内で参照される画像を直接表示するためのルート"""
    user_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.username)
    return send_from_directory(user_upload_folder, secure_filename(filename))

@bp.route('/ForgeGrid/upload_image', methods=['POST'])
@login_required
def upload_image():
    """クリップボードからペーストされた画像をBase64形式で受け取り、画像ファイルとして保存し、Markdown形式の画像タグを返すAPIエンドポイント"""
    data = request.get_json()
    if 'image' not in data:
        return jsonify({'error': '画像データがありません。'}), 400
    
    base64_image = data['image']
    image_data = base64.b64decode(base64_image.split(',')[1])
    
    filename = f"{uuid.uuid4()}.png"
    user_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.username)
    os.makedirs(user_upload_folder, exist_ok=True)
    filesave_path = os.path.join(user_upload_folder, filename)
    
    with open(filesave_path, "wb") as fh:
        fh.write(image_data)
        
    markdown = f"![ScreenShot]({filename})"
    return jsonify({'markdown': markdown})

# --- パスワード変更関連 ---
@bp.route('/ForgeGrid/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not check_password_hash(current_user.password, current_password):
            flash('現在のパスワードが正しくありません。', category='danger')
            return redirect(url_for('views.change_password'))

        if new_password != confirm_password:
            flash('新しいパスワードと確認用パスワードが一致しません。', category='danger')
            return redirect(url_for('views.change_password'))

        if len(new_password) < 6:
            flash('パスワードは6文字以上で入力してください。', category='danger')
            return redirect(url_for('views.change_password'))

        current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        
        flash('パスワードが正常に変更されました。', category='success')
        return redirect(url_for('views.home'))

    return render_template('change_password.html', logged_user=current_user.username)