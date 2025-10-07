import os
import uuid
import time

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, g

from database import fetch_all, run_query, SELECT_PROJECTS_SQL, INSERT_PROJECT_SQL, DELETE_PROJECT_BY_ID_SQL

project = Blueprint('project', __name__, template_folder='templates')

def insert_project(title: str, description: str, img: str, link: str, lifespan: str) -> int:
    post_id = int(time.time())
    run_query(INSERT_PROJECT_SQL, [post_id, title, description, img, link, lifespan])
    return post_id

def delete_project(post_id: int) -> None:
    run_query(DELETE_PROJECT_BY_ID_SQL, [post_id])


@project.route('/')
def explore():
    return render_template("projects.html", projects=fetch_all(SELECT_PROJECTS_SQL))