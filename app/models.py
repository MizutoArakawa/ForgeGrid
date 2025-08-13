"""
このファイルはデータベースの根幹の設定である。
ユーザと作成したノードを紐づけるデータベースの中身を定義している。
"""

# SQLAlchemy: FlaskアプリケーションでSQLAlchemyを使用するための拡張機能。データベース操作をより簡単に実行することが可能
from flask_sqlalchemy import SQLAlchemy

# UserMixin: Flask-Loginでユーザーモデルに含める必要がある基本的なプロパティとメソッドを提供
from flask_login import UserMixin

# DeclarativeBase: SQLAlchemy ORMでモデルを定義するための基底クラス
# Mapped, mapped_column: SQLAlchemy 2.0スタイルでカラムと関係をマップするために使用
# relationship: データベーステーブル間の関係（例：一対多）を定義するために使用
# Integer, String, Column, Text: SQLAlchemyでデータベースのカラム型を定義するために使用
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Column, Text, ForeignKey



# SQLAlchemyのインスタンスを作成
# __init__.pyでアプリケーションと紐付けます
class Base(DeclarativeBase):
    pass

# model_classに先ほど定義したBaseクラスを指定することで、新しい宣言的スタイルを使用
db = SQLAlchemy(model_class=Base)

class User(UserMixin, db.Model):
    """
    ユーザー情報を格納するデータベースモデル
    Flask-LoginのUserMixinを継承することで、ログイン管理に必要なプロパティとメソッドを提供
    """
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    
    # UserとNoteのリレーションシップを定義
    notes = relationship("Note", back_populates="user")

class Note(db.Model):
    """メモ（ノート）の情報を格納するデータベースモデル
    ユーザーに紐づけられる
    """
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    content: Mapped[str] = Column(Text, nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    
    # usersテーブルのidを外部キーとして設定
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    
    # UserとNoteのリレーションシップを定義
    user = relationship("User", back_populates="notes")
