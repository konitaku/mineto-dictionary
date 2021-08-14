from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email
from flask_ckeditor import CKEditorField


class LoginForm(FlaskForm):
    email = StringField(label="メールアドレス",
                        validators=[DataRequired(message="値を入力してください"), Email(message="無効なメールアドレスです")])
    password = PasswordField(label="パスワード", validators=[DataRequired(message="値を入力してください")])
    submit = SubmitField(label="ログイン")


class RegisterForm(FlaskForm):
    name = StringField(label="ユーザーネーム", validators=[DataRequired(message="値を入力してください")]
                       # ,render_kw={"placeholder": "例) パンナコッタ、トマトの逆襲"}
                       )
    email = StringField(label="メールアドレス",
                        validators=[DataRequired(message="値を入力してください"), Email(message="無効なメールアドレスです")]
                        # ,render_kw={"placeholder": "example@email.com"}
                        )
    password = PasswordField(label="パスワード", validators=[DataRequired(message="値を入力してください")],
                             render_kw={"placeholder": "英数字、記号を使って12文字以上で入力してください"})
    submit = SubmitField(label="登録")


class ArticleForm(FlaskForm):
    title = StringField(label="単語・用語", validators=[DataRequired(message="値を入力してください")],
                        render_kw={"placeholder": "登録したい言葉を入力してください"}
                        )
    subtitle = StringField(label="ふりがな",
                           validators=[DataRequired(message="値を入力してください")],
                           render_kw={"placeholder": "ふりがなを入力してください"}
                           )
    tags = StringField(label="タグ",
                       validators=[DataRequired(message="値を入力してください")],
                       id="tagsInput"
                       )
    body = CKEditorField(label="説明文",
                         validators=[DataRequired(message="値を入力してください")],
                         render_kw={"placeholder": "言葉を説明する記事（書き方は自由です）"}
                         )
    edit_summary = StringField(label="編集内容の要約")
    submit = SubmitField(label="登録")


class CommentForm(FlaskForm):
    text = TextAreaField(label="コメント", validators=[DataRequired(message="コメントを入力してください")],
                         render_kw={"placeholder": "コメントを入力してください"})
    submit = SubmitField(label="送信")
