import os
import time

import requests
from flask import Blueprint, request, render_template, redirect, url_for, flash
from datetime import datetime
from database import get_db, run_query, fetch_one, fetch_all, SELECT_VISIBLE_VISITOR_POSTS_SQL, SELECT_HIDDEN_VISITOR_POSTS_SQL, \
    SELECT_VISITOR_POST_BY_ID_SQL, INSERT_VISITOR_POST_SQL, DELETE_VISITOR_POST_BY_ID_SQL, MARK_VISIBLE_VISITOR_POST_SQL

COLORS = ["rosewater", "flamingo", "pink", "mauve", "red", "maroon", "peach", "yellow", "green", "teal", "sky", "sapphire", "blue", "lavender"]

visitor = Blueprint('visitor', __name__, template_folder='templates')

# int, str, str, str, bool, datetime
def fetch_all_visitors(visible: bool = True) -> list[tuple]:
    return fetch_all(SELECT_VISIBLE_VISITOR_POSTS_SQL if visible else SELECT_HIDDEN_VISITOR_POSTS_SQL)

def insert_post(author: str, color: str, content: str) -> int:
    post_id = int(time.time())
    run_query(INSERT_VISITOR_POST_SQL, [post_id, author, color, content])
    return post_id

def approve_post(visitor_id: int) -> None:
    run_query(MARK_VISIBLE_VISITOR_POST_SQL, [visitor_id])

def deny_post(visitor_id: int) -> None:
    run_query(DELETE_VISITOR_POST_BY_ID_SQL, [visitor_id])

@visitor.route('/visitor')
def submit():  # put application's code here
    return render_template("visitor.html", colors=COLORS)

def validate_post(name: str, color: str, message: str) -> str | None:
    if len(name) < 3 or len(name) > 24:
        return "Invalid name length!"
    if color not in COLORS:
        return "Invalid color!"
    if len(message) < 16 or len(message) > 256:
        return "Invalid message length!"
    return None

@visitor.route('/visitor/post', methods=['POST'])
def post():  # put application's code here
    secret = os.getenv('CLOUDFLARE_SECRET')
    response = request.form.get('cf-turnstile-response')

    r = requests.post("https://challenges.cloudflare.com/turnstile/v0/siteverify", data={
        'secret': secret,
        'response': response,
    })
    res = r.json()

    if  res['success']:
        name = request.form.get("name")
        color = request.form.get("color")
        message = request.form.get("message")

        err = validate_post(name, color, message)
        if not err:
            requests.post(os.getenv('DISCORD_WEBHOOK'), data={"content": f"**{name}** sent in a message: ```{message}```"})

            flash("Your post is under review, thanks!", "success")
            insert_post(name, color, message)
            return redirect(url_for("home"))
        flash(err, "error")

    return redirect(url_for('visitor.submit'))


