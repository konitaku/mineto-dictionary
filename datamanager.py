from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime


def create_get_db(app):
    db = SQLAlchemy(app)

    class User(UserMixin, db.Model):
        __tablename__ = "users"
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(250), nullable=False)
        email = db.Column(db.String(250), unique=True, nullable=False)
        self_intro = db.Column(db.Text)
        password = db.Column(db.String(250), nullable=False)
        # image_url = db.Column(db.String(250))
        # ////////////////////////////////////////////////
        articles = db.relationship("EditorLog", backref="user")
        comments = db.relationship("Comment", backref="user")
        likes = db.relationship("LikeLog", backref="user")

    class Article(db.Model):
        __tablename__ = "articles"
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(250), nullable=False)
        subtitle = db.Column(db.String(250))
        body = db.Column(db.Text)
        init_datetime = db.Column(db.DateTime, default=datetime.utcnow)
        updated_datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        # ////////////////////////////////////////////////
        comments = db.relationship("Comment", backref="parent_article")
        editor_logs = db.relationship("EditorLog", backref="article")
        likes = db.relationship("LikeLog", backref="article")
        tags = db.relationship("TagController", backref="article")

    class Tag(db.Model):
        __tablename__ = "tags"
        id = db.Column(db.Integer, primary_key=True)
        tag_name = db.Column(db.String(250), nullable=False)
        articles = db.relationship("TagController", backref="tag")
        date = db.Column(db.DateTime, default=datetime.utcnow)

    class Comment(db.Model):
        __tablename__ = "comments"
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
        article_id = db.Column(db.Integer, db.ForeignKey("articles.id"))
        text = db.Column(db.Text)
        init_datetime = db.Column(db.DateTime, default=datetime.utcnow)
        updated_datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class EditorLog(db.Model):
        __tablename__ = 'editor_log'
        __table_args__ = {'extend_existing': True}
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
        article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
        initial_create = db.Column(db.Boolean)
        edit_summary = db.Column(db.Text, default="編集の要約なし")
        editor_name = db.Column(db.String)
        date = db.Column(db.DateTime, default=datetime.utcnow)

    class LikeLog(db.Model):
        __tablename__ = "like_log"
        __table_args__ = {'extend_existing': True}
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
        article_id = db.Column(db.Integer, db.ForeignKey("articles.id"))
        ip_address = db.Column(db.String)
        date = db.Column(db.DateTime, default=datetime.utcnow)

    class TagController(db.Model):
        __tablename__ = "tags_controller"
        id = db.Column(db.Integer, primary_key=True)
        tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"))
        article_id = db.Column(db.Integer, db.ForeignKey("articles.id"))
        date = db.Column(db.DateTime, default=datetime.utcnow)

    # db.drop_all()
    db.create_all()
    return [db, User, Article, EditorLog, LikeLog, Comment, Tag, TagController]
