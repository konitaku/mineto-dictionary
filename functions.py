import re
from mineto import db, Tag, TagController, Article, LikeLog, EditorLog
from datetime import datetime, timedelta
from flask import request
from flask_login import current_user


def body_to_description(body: str) -> str:
    try:
        p = re.compile(r"<[^>]*?>")
        final_result = p.sub("", body)
        # pタグから始まる文字列を取得
        # x = re.search(r'<p>(.*)', body, flags=re.DOTALL)
        # result = body[x.span()[0] + 3: x.span()[1]]
        # print(result)

        # pの終了タグまででキリトリ
        # y = re.match(r'(.*)</p>', result, flags=re.DOTALL)
        # final_result = result[y.span()[0]: y.span()[1] - 4]
        # final_result = body
    except AttributeError:
        final_result = ""

    # 説明文の先頭から50文字だけ渡す
    # print(final_result)
    return final_result[:50]


def register_tags_to_db(tags, article_obj):
    for tag in tags.split(","):
        tag_data = db.session.query(Tag).filter_by(tag_name=tag).first()
        # 新しいタグ名だったら新規タグデータを作成
        if not tag_data:
            tag_data = Tag()
            tag_data.tag_name = tag
            db.session.add(tag_data)
            db.session.commit()

        # 記事が持ってるタグ名をリストにする
        tags_article_has = []
        if article_obj.tags:
            for tag_obj in article_obj.tags:
                tags_article_has.append(tag_obj.tag.tag_name)

                # 削除されたタグがあれば記事データから消しとく
                if tag_obj.tag.tag_name not in tags.split(","):
                    db.session.delete(tag_obj)
                    db.session.commit()

        # 新しいタグたちを記事データに追加
        if tag_data.tag_name not in tags_article_has:
            tag_controller = TagController()
            tag_controller.tag_id = tag_data.id
            tag_controller.article_id = article_obj.id
            db.session.add(tag_controller)
            db.session.commit()


def calc__updated_time(article_obj: Article):
    newest_date = article_obj.editor_logs[0].date
    for editor_log in article_obj.editor_logs:
        if newest_date < editor_log.date:
            newest_date = editor_log.date
    newest_date += timedelta(hours=9)
    result = newest_date.strftime("%Y/%m/%d")
    # print(result)
    return result


def liked_or_not(article_id) -> bool:
    if current_user.is_authenticated:
        like_log = LikeLog.query.filter(LikeLog.user_id == current_user.id)\
            .filter(LikeLog.article_id == article_id).first()
        if like_log:
            return True
    else:
        ip = get__ip_address()
        like_log = LikeLog.query.filter(LikeLog.ip_address == ip) \
            .filter(LikeLog.article_id == article_id).first()
        if like_log:
            return True
    return False


def get__ip_address():
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    return ip


def make_edit_log_sorted_by_latest_date(article_obj: Article):
    result_list = sorted(article_obj.editor_logs, key=lambda x: x.date)
    # print(result_list[-1].date)
    return result_list[-1]


def translate_log_to_date(editor_log: EditorLog):
    duration = datetime.utcnow() - editor_log.date
    # print(duration)
    if duration < timedelta(hours=1):
        return f"{str(duration).split(':')[1]}分前"
    elif duration < timedelta(hours=24):
        return f"{str(duration).split(':')[0]}時間前"
    elif duration < timedelta(days=7):
        return f"{duration.days}日前"
    else:
        return f"{(editor_log.date + timedelta(hours=9)).strftime('%Y/%m/%d')}"
