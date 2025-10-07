import os
import uuid

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, g, send_from_directory

from blog import delete_post, insert_post
from visitor import fetch_all_visitors, approve_post, deny_post
from project import insert_project, delete_project

admin = Blueprint('admin', __name__, template_folder='templates/admin')
STATUS = "online"

@admin.before_request
def blueprint_before_request():
    if request.cookies.get('Parental-Control') != os.getenv('FLASK_SECRET_KEY'):
        abort(401)

@admin.route('/')
def couch():
    return render_template("couch.html")

@admin.route('/visitor')
def visitors():
    return render_template("visitors.html", posts=fetch_all_visitors(False))

@admin.route('/visitor/approve/<int:visitor_id>')
def approve_visitor(visitor_id: int):
    approve_post(visitor_id)
    flash("Successfully approved!", "success")
    return redirect(url_for('admin.visitors'))

@admin.route('/visitor/deny', methods=['POST'])
def deny_visitor():
    deny_post(int(request.form.get('id')))
    flash("Successfully removed!", "success")
    return redirect(url_for('admin.visitors'))


@admin.route('/journal')
def journal():
    return render_template("journal.html")

@admin.route('/journal/post', methods=['POST'])
def post_article():
    post_id = insert_post(request.form.get('img'), request.form.get('title'), request.form.get('description'), request.form.get('content'))
    flash("Successfully posted!", "success")
    return redirect(url_for('blog.view', post_id=post_id))

@admin.route('/journal/remove', methods=['POST'])
def remove_article():
    delete_post(int(request.form.get('id')))
    flash("Successfully deleted!", "success")
    return redirect(url_for('admin.journal'))

@admin.route('/project')
def project():
    return render_template("project.html")

@admin.route('/project/post', methods=['POST'])
def post_project():
    insert_project(request.form.get('title'), request.form.get('description'), request.form.get('thumbnail'), request.form.get('link'), request.form.get('lifespan'))
    flash("Successfully posted!", "success")
    return redirect(url_for('project.explore'))

@admin.route('/project/remove', methods=['POST'])
def remove_project():
    delete_project(int(request.form.get('id')))
    flash("Successfully deleted!", "success")
    return redirect(url_for('admin.project'))

@admin.route('/upload', methods=['POST'])
def upload_file():
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '':
            filename = str(uuid.uuid4()) + "." + file.filename.rsplit('.', 1)[1].lower()
            folder_path = f"data/assets"
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            file.save(os.path.join(folder_path, filename))
            url = url_for('send_assets', path=filename)
            flash(f"Uploaded as <a href=\"{url}\">{url}</a>!", "success")
            return redirect(url_for("admin.couch"))
        else:
            return "Filename is empty"
    else:
        return "No file found"

@admin.route('/status', methods=['POST'])
def status():
    status = request.form.get('status')
    flash(f"Set status to {STATUS}!", "success")
    return redirect(url_for("admin.couch"))
