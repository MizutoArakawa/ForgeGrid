# Flask-WTFからFlaskFormをインポート
# FlaskFormは、WTFormsとFlaskを連携させるための基底クラスで、CSRF（クロスサイトリクエストフォージェリ）保護などの機能を提供
from flask_wtf import FlaskForm

# WTFormsから必要なフィールドタイプをインポート
# StringField: ユーザー名や一般的なテキスト入力など、単一行の文字列を入力するためのフィールド
# PasswordField: パスワード入力用のフィールド。入力された文字がアスタリスクなどで隠される
# SubmitField: フォームを送信するためのボタン（「ログイン」や「登録」など）を作成
from wtforms import StringField, PasswordField, SubmitField

# WTFormsのバリデーター（入力検証ルール）をインポート
# DataRequired(): フィールドが空であってはならないことを示すバリデーター。ユーザーがこのフィールドに何か入力しないとフォームは送信不可
from wtforms.validators import DataRequired, EqualTo, ValidationError

from .models import User


class LoginForm(FlaskForm):
    """
    ログインフォームを定義するクラス
    FlaskFormを継承しており、ユーザー名とパスワードの入力を受け付ける
    """
    username = StringField(label='ユーザー名', validators=[DataRequired()])
    password = PasswordField(label="パスワード", validators=[DataRequired()])
    submit = SubmitField(label="ログイン")
    
class RegisterForm(FlaskForm):
    """
    新規ユーザー登録フォームを定義するクラス。
    新しいユーザー名とパスワードの入力を受け付ける
    """
    username = StringField(label='ユーザー名', validators=[DataRequired()])
    password = PasswordField(label="パスワード", validators=[DataRequired()])
    
    # ここにconfirm_passwordフィールドを追加
    confirm_password = PasswordField(
        "パスワード確認", 
        validators=[
            DataRequired(),
            EqualTo('password', message='パスワードが一致しません')
        ]
    )
    submit = SubmitField(label="登録")

    def validate_username(self, username):
        """ユーザー名の重複チェック"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('このユーザー名はすでに使用されています。')