import time
import markdown
from flask import Blueprint, abort, render_template
from datetime import datetime, UTC
from database import get_db, run_query, fetch_one, fetch_all, SELECT_BLOG_POSTS_SQL, SELECT_BLOG_POST_BY_ID_SQL, INSERT_BLOG_POST_SQL, DELETE_BLOG_POST_BY_ID_SQL

blog = Blueprint('blog', __name__, template_folder='templates/blog')

# str, str, str, str, str, datetime
def fetch_all_posts() -> list[tuple]:
    return fetch_all(SELECT_BLOG_POSTS_SQL)

def fetch_specific_post(post_id: int) -> tuple:
    return fetch_one(SELECT_BLOG_POST_BY_ID_SQL, [post_id])

def insert_post(img: str, title: str, description: str, content: str) -> int:
    post_id = int(time.time())
    run_query(INSERT_BLOG_POST_SQL, [post_id, img, title, description, content])
    return post_id


def delete_post(post_id: int) -> None:
    run_query(DELETE_BLOG_POST_BY_ID_SQL, [post_id])

@blog.route('/')
def explore():
    return render_template("explore.html", posts=fetch_all_posts())

@blog.route('/<int:post_id>')
def view(post_id: int):
    post = fetch_specific_post(post_id)
    if post is None:
        abort(404)
    return render_template("post.html", post=post, content=markdown.markdown(post[4]))