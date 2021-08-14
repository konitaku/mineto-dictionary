from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import LoginManager, login_user, logout_user
from forms import LoginForm, RegisterForm, ArticleForm, CommentForm
from datamanager import create_get_db
import os
from functions import *

# key = os.urandom(24)
# print(key)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///mineto.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY",
                                          '\xc0\xa9\x18\xfaTT1\xb4\x90\xaam2>\xa8/\x7fM\x88\xda\xf7\x07\x81g"')
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
ckeditor = CKEditor(app)
login_manager = LoginManager(app)
# データベースの情報を取得
data_manager = create_get_db(app)
db = data_manager[0]
User = data_manager[1]
Article = data_manager[2]
EditorLog = data_manager[3]
LikeLog = data_manager[4]
Comment = data_manager[5]
Tag = data_manager[6]
TagController = data_manager[7]


@login_manager.user_loader
def load_user(user_id):
    print(user_id)
    return User.query.get(user_id)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search", methods=["post", "get"])
def search():
    if request.method == "POST":
        search_word__list = request.form.get("search").split()
        result__list = []
        for search_word in search_word__list:
            if "p" in search_word or "h" in search_word:
                result = Article.query.filter(
                    Article.title.contains(search_word) |  # # "|" means "or"
                    Article.subtitle.contains(search_word)
                ).all()
            else:
                result = Article.query.filter(
                    Article.title.contains(search_word) |  # # "|" means "or"
                    Article.subtitle.contains(search_word)
                    | Article.body.contains(search_word)
                ).all()

            for article_ in result:
                if article_ not in result__list:
                    result__list.append(article_)
        result__list.sort(key=lambda x: x.subtitle)
        # print(result__list)
        return render_template("search.html", result__list=result__list, body_to_description=body_to_description,
                               search_word=",".join(search_word__list))
    else:
        result__list = Article.query.all()
        result__list.sort(key=lambda x: x.subtitle)
        # print(result__list)
        return render_template("search.html", result__list=result__list, body_to_description=body_to_description,
                               search_word="Mineto一覧")


@app.route("/tag-search/<tag_id>")
def tag_search(tag_id):
    target_tag = Tag.query.get(tag_id)
    if target_tag:
        tags = TagController.query.filter_by(tag_id=tag_id).all()
        result__list = []
        for tag_controller in tags:
            result__list.append(tag_controller.article)

        result__list.sort(key=lambda x: x.subtitle)
    # print(result__list)
        return render_template("search.html",
                               result__list=result__list,
                               body_to_description=body_to_description,
                               search_word=f"タグ検索<br>「{target_tag.tag_name}」")
    else:
        flash("このタグは存在しません", "error")
        return redirect(url_for("home"))


@app.route("/article/<article_id>", methods=["post", "get"])
def article(article_id):
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(user_id=current_user.id, article_id=article_id, text=form.text.data)
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for("article", article_id=article_id))
    article_data = Article.query.get(article_id)
    is_liked = liked_or_not(article_id)
    if article_data:
        init_datetime = (article_data.init_datetime + timedelta(hours=9)).strftime("%Y/%m/%d")
        updated_datetime = calc__updated_time(article_data)
        latest_log = make_edit_log_sorted_by_latest_date(article_data)
        duration = translate_log_to_date(latest_log)
        return render_template("article.html", article_data=article_data,
                               init_datetime=init_datetime, updated_datetime=updated_datetime,
                               is_liked=is_liked, latest_log=latest_log, duration=duration,
                               form=form)
    else:
        flash("記事がありません", category="error")
        return redirect(url_for("home"))


@app.route("/delete-comment/<comment_id>")
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment:
        article_id = comment.article_id

        db.session.delete(comment)
        db.session.commit()
        return redirect(url_for("article", article_id=article_id))
    else:
        flash("選択されたコメントデータはありませんでした。", "error")
        return redirect(url_for("home"))


@app.route("/edit-comment/<comment_id>", methods=["post", "get"])
def edit_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment:
        article_id = comment.article_id
        form = CommentForm(text=comment.text)
        if form.validate_on_submit():
            comment.text = form.text.data
            db.session.commit()
            return redirect(url_for("article", article_id=article_id))
        return render_template("edit-comment.html", form=form)
    else:
        flash("コメントはありません", "error")
        return redirect(url_for("home"))


@app.route("/like-count/<article_id>", methods=["POST", "GET"])
def js_like_count(article_id):
    if request.method == "POST":
        if current_user.is_authenticated:
            current_like_log = LikeLog.query.filter(
                LikeLog.article_id == article_id).filter(
                LikeLog.user_id == current_user.id).first()
            if current_like_log:
                db.session.delete(current_like_log)
                db.session.commit()
                state = False
            else:
                like_log = LikeLog(article_id=article_id, user_id=current_user.id)
                db.session.add(like_log)
                db.session.commit()
                state = True
        else:
            ip = get__ip_address()

            current_like_log = LikeLog.query.filter(
                LikeLog.article_id == article_id).filter(
                LikeLog.ip_address == ip).first()
            if current_like_log:
                db.session.delete(current_like_log)
                db.session.commit()
                state = False
            else:
                like_log = LikeLog(article_id=article_id, ip_address=ip)
                db.session.add(like_log)
                db.session.commit()
                state = True

        target_article = Article.query.get(article_id)
        return {"state": state, "total": len(target_article.likes)}


@app.route("/page-log/<article_id>")
def page_log(article_id):
    target_article = Article.query.get(article_id)
    return render_template("page_log.html", article=target_article, timedelta=timedelta)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user)
                return redirect(url_for("home"))
            else:
                flash("パスワードが間違っています", "error")
        else:
            flash("メールアドレスが間違っています", "error")
    return render_template("login.html", form=form)


@app.route(f"/n-login/<next_url>/<article_id>", methods=["post", "get"])
def login_with_next(next_url, article_id):
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user)
                if article_id != 0:
                    return redirect(url_for(next_url, article_id=article_id))
                else:
                    return redirect(url_for(next_url))
            else:
                flash("パスワードが間違っています", "error")
        else:
            flash("メールアドレスが間違っています", "error")
    return render_template("login.html", form=form)


@app.route("/n-register/<next_url>/<article_id>", methods=["post", "get"])
def register_with_next(next_url, article_id):
    form = RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        if not db.session.query(User).filter_by(email=form.email.data).first():
            new_user = User()
            new_user.name = form.name.data
            new_user.email = form.email.data
            new_user.password = form.password.data
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            if article_id != 0:
                return redirect(url_for(next_url, article_id=article_id))
            else:
                return redirect(url_for(next_url))
        else:
            flash("このメールアドレスは既に登録されています", category="error")
            flash("こちらのページからログインしてください", category="error")
            return redirect(url_for('login_with_next', next_url=next_url, article_id=article_id))
    return render_template("register.html", form=form, next_url=next_url)


@app.route("/register", methods=["POST", "get"])
def register():
    form = RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        if not db.session.query(User).filter_by(email=form.email.data).first():
            new_user = User()
            new_user.name = form.name.data
            new_user.email = form.email.data
            new_user.password = form.password.data
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for("home"))
        else:
            flash("このメールアドレスは既に登録されています", category="error")
            flash("こちらのページからログインしてください", category="error")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/create-article", methods=["post", "get"])
def create_article():
    form = ArticleForm()
    if request.method == "POST" and form.validate_on_submit():
        # # h1, h2 タグを h3 タグに置き換え
        # form_body_data = form.body.data
        # x = form_body_data.replace("<h1>", "<h3 class='h1'>")
        # y = x.replace("<h2>", "<h3 class='h2'>")
        # z = y.replace("</h1>", "</h3>")
        # xx = z.replace("</h2>", "</h3>")

        # 記事データを登録
        new_article = Article()
        new_article.title = form.title.data
        new_article.subtitle = form.subtitle.data
        new_article.body = form.body.data
        db.session.add(new_article)
        db.session.commit()

        # 記事の編集ログを記録
        editor_log = EditorLog(article_id=new_article.id, edit_summary="新規作成", initial_create=True)
        # ユーザーがログインしている場合、ユーザー名を登録
        if current_user.is_authenticated:
            editor_log.user_id = current_user.id
            editor_log.editor_name = current_user.name
        else:
            # そうでなければ編集者のIPアドレスを取得し、それを編集者名に登録
            if request.headers.getlist("X-Forwarded-For"):
                ip = request.headers.getlist("X-Forwarded-For")[0]
            else:
                ip = request.remote_addr
            editor_log.editor_name = ip
        # データベースに追加
        db.session.add(editor_log)
        db.session.commit()

        # タグデータを登録
        register_tags_to_db(form.tags.data, new_article)
        return redirect(url_for("home"))
    # 全タグ名を編集ページのTagify.jsに渡す
    all_tag_data = Tag.query.all()
    all_tag_name = []
    for tag_data in all_tag_data:
        all_tag_name.append(tag_data.tag_name)

    return render_template("edit.html", form=form, all_tag_name=all_tag_name)


@app.route("/edit-article/<article_id>", methods=["post", "get"])
def edit_article(article_id):
    # 編集対象の記事をデータベースから取得
    target_article = Article.query.get(article_id)
    print(target_article)
    if target_article:
        # タグデータをデータベースオブジェクトからリストへ変換
        tags = []
        for tag_log in target_article.tags:
            tags.append(tag_log.tag.tag_name)

        # # h1, h2 タグを h3 タグに置き換え
        # body_data = target_article.body
        # x = body_data.replace("<h3 class='h1'>", "<h1>")
        # y = x.replace("<h3 class='h2'>", "<h2>")
        # z = y.replace("</h3>", "</h1>")
        # xx = z.replace("</h3>", "</h2>")

        # 編集フォームに元の記事データを渡す
        form = ArticleForm(
            title=target_article.title,
            subtitle=target_article.subtitle,
            body=target_article.body,
            tags=",".join(tags)
        )

        if form.validate_on_submit():
            # # h1, h2 タグを h3 タグに置き換え
            # form_body_data = form.body.data
            # x = form_body_data.replace("<h1>", "<h3 class='h1'>")
            # y = x.replace("<h2>", "<h3 class='h2'>")
            # z = y.replace("</h1>", "</h3>")
            # xx = z.replace("</h2>", "</h3>")

            # postされた新しい記事データをデータベースに更新
            target_article.title = form.title.data
            target_article.subtitle = form.subtitle.data
            target_article.body = form.body.data
            db.session.commit()
            register_tags_to_db(form.tags.data, target_article)

            # 記事の編集ログを記録
            editor_log = EditorLog(
                article_id=target_article.id,
                initial_create=False
            )
            if form.edit_summary.data:
                editor_log.edit_summary = form.edit_summary.data

            # ユーザーがログインしている場合、ユーザー名を登録
            if current_user.is_authenticated:
                editor_log.user_id = current_user.id
                editor_log.editor_name = current_user.name
            else:
                # そうでなければ編集者のIPアドレスを取得し、それを編集者名に登録
                if request.headers.getlist("X-Forwarded-For"):
                    ip = request.headers.getlist("X-Forwarded-For")[0]
                else:
                    ip = request.remote_addr
                editor_log.editor_name = ip
            # データベースに追加
            db.session.add(editor_log)
            db.session.commit()
            return redirect(url_for("article", article_id=target_article.id))

        # 全タグ名を編集ページのTagify.jsに渡す
        all_tag_data = Tag.query.all()
        all_tag_name = []
        for tag_data in all_tag_data:
            all_tag_name.append(tag_data.tag_name)
        return render_template("edit.html", form=form, article_id=article_id, all_tag_name=all_tag_name, is_edit=True)
    else:
        return redirect(url_for("home"))


@app.route("/user/<user_info>")
def user_data(user_info):
    user = User.query.get(user_info)
    if user:
        print(user)
        return render_template("user.html", user=user, is_user=True,
                               body_to_description=body_to_description)
    else:
        print("not user")
        edit_logs = EditorLog.query.filter(EditorLog.editor_name == user_info).all()
        like_logs = LikeLog.query.filter(LikeLog.ip_address == user_info).all()
        return render_template("user.html",
                               user_info=user_info, edit_logs=edit_logs, like_logs=like_logs, is_user=False,
                               body_to_description=body_to_description)


@app.route("/get-user-data/<user_id>", methods=["post"])
def get_user_data(user_id):
    user = User.query.get(user_id)
    username = user.name
    self_intro = user.self_intro
    return {"username": username, "self_intro": self_intro}


@app.route("/save-new-user-data", methods=["post"])
def save_new_user_data():
    if request.method == "POST":
        new_user_data = eval(request.get_data())
        print(new_user_data["username"])
        print(new_user_data["self_intro"])
        user = User.query.get(current_user.id)
        user.name = new_user_data["username"]
        user.self_intro = new_user_data["self_intro"]
        db.session.commit()
        return {"response": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
