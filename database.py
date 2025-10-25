import os.path
import sqlite3
import time
from sqlite3 import Cursor

from flask import g

CREATE_BLOG_TABLE_SQL = "CREATE TABLE blog ( \
    id INTEGER PRIMARY KEY, \
    img text, \
    title text, \
    description text, \
    content text, \
    posted TIMESTAMP)"
INSERT_BLOG_POST_SQL = "INSERT INTO blog (id, img, title, description, content, posted) VALUES (?,?,?,?,?,DATETIME())"
SELECT_BLOG_POSTS_SQL = "SELECT * FROM blog ORDER BY id DESC;"  # The "id"s are really just unix timestamps
SELECT_BLOG_POST_BY_ID_SQL = "SELECT * FROM blog WHERE id = ?"
DELETE_BLOG_POST_BY_ID_SQL = "DELETE FROM blog WHERE id = ?"

CREATE_VISITOR_TABLE_SQL = "CREATE TABLE visitors ( \
    id INTEGER PRIMARY KEY, \
    author text, \
    color text, \
    content text, \
    visible boolean, \
    posted TIMESTAMP)"
INSERT_VISITOR_POST_SQL = "INSERT INTO visitors (id, author, color, content, visible, posted) VALUES (?,?,?,?,false,DATETIME())"
SELECT_HIDDEN_VISITOR_POSTS_SQL = "SELECT * FROM visitors WHERE visible = false ORDER BY id DESC;"  # The "id"s are really just unix timestamps
SELECT_VISIBLE_VISITOR_POSTS_SQL = "SELECT * FROM visitors WHERE visible = true ORDER BY id DESC;"
SELECT_VISITOR_POST_BY_ID_SQL = "SELECT * FROM visitors WHERE id = ?"
DELETE_VISITOR_POST_BY_ID_SQL = "DELETE FROM visitors WHERE id = ?"
MARK_VISIBLE_VISITOR_POST_SQL = "UPDATE visitors SET visible = true WHERE id = ?"

CREATE_PROJECT_TABLE_SQL = "CREATE TABLE projects ( \
    id INTEGER PRIMARY KEY, \
    title text, \
    description text, \
    img text, \
    link text, \
    lifespan text)"
INSERT_PROJECT_SQL = "INSERT INTO projects (id, title, description, img, link, lifespan) VALUES (?,?,?,?,?,?)"
DELETE_PROJECT_BY_ID_SQL = "DELETE FROM projects WHERE id = ?"
SELECT_PROJECTS_SQL = "SELECT * FROM projects ORDER BY id DESC;"

CREATE_CUSTOM_TABLE_SQL = "CREATE TABLE custom ( \
    name text PRIMARY KEY, \
    destination text)"
INSERT_CUSTOM_SQL = "INSERT INTO custom (name, destination) VALUES (?,?)"
DELETE_CUSTOM_SQL = "DELETE FROM custom WHERE name = ?"
GET_CUSTOM_SQL = "SELECT destination FROM custom WHERE name = ?"

if not os.path.exists("data"):
    os.mkdir("data")
if not os.path.exists('data/assets'):
    os.mkdir('data/assets')

DATABASE_FILE = "data/sylvie.db"

def initialize_db():
    db = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = db.cursor()
    try:
        cursor.execute(CREATE_CUSTOM_TABLE_SQL)
        cursor.execute(CREATE_BLOG_TABLE_SQL)
        cursor.execute(CREATE_VISITOR_TABLE_SQL)
        cursor.execute(CREATE_PROJECT_TABLE_SQL)
        with open("templates/hello_world.md", "r", encoding="utf-8") as post_file:
            cursor.execute(INSERT_BLOG_POST_SQL,
                           [int(time.time()),
                            "assets/icons/globe.png",
                            "hello world!",
                            "this is my site, welcome back!",
                            post_file.read()])
        db.commit()
    except sqlite3.OperationalError:
        pass
    return db

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = initialize_db()
        setattr(g, "_database", db)
    return db

def run_query(query: str, params: list = None, grab_one: bool = False, grab_all: bool = False) -> tuple | list[tuple] | None:
    if params is None:
        params = []
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, params)
    db.commit()

    return_value = None
    if grab_one:
        return_value = cursor.fetchone()
    if grab_all:
        return_value = cursor.fetchall()
    cursor.close()

    return return_value

def fetch_one(query: str, params: list = None) -> tuple:
    return run_query(query, params, grab_one=True)

def fetch_all(query: str, params: list = None) -> list[tuple]:
    return run_query(query, params, grab_all=True)