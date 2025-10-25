from database import run_query, fetch_one, GET_CUSTOM_SQL, INSERT_CUSTOM_SQL, DELETE_CUSTOM_SQL
from flask import Blueprint, abort, redirect

custom = Blueprint('custom', __name__)

@custom.route('/<string:name>')
def index(name: str):
    fetched = fetch_one(GET_CUSTOM_SQL, [name])
    if fetched is None:
        abort(404)
    return redirect(fetched[0])

def insert_custom_route(name: str, destination: str):
    run_query(INSERT_CUSTOM_SQL, [name, destination])

def delete_custom_route(name: str):
    run_query(DELETE_CUSTOM_SQL, [name])