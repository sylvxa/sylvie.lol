import os

import pytz
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, send_from_directory, g, render_template, url_for, redirect
from datetime import datetime

from admin import admin
from blog import blog
from visitor import visitor, fetch_all_visitors
from project import project

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.register_blueprint(admin, url_prefix='/meeeeeeee')
app.register_blueprint(blog, url_prefix='/journal') # yeah, i'm branding it as journal because blog sounds *obtuse*
app.register_blueprint(project, url_prefix='/projects')
app.register_blueprint(visitor)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

TIMEZONE = pytz.timezone('America/Chicago')
@app.before_request
async def load_global_data():
    now = datetime.now(TIMEZONE)
    g.local_time = now.strftime("%H:%M")
    if now.hour < 7: # Too lazy to figure out actual statuses, sorry!
        g.status = "offline"
    else:
        g.status = "online"

@app.teardown_appcontext
def close_connection(_):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

BUTTONS = None
BUTTON_DIRECTORY = 'buttons'

# error handling
@app.errorhandler(404)
def page_not_found(_):
    return render_template("error.html", error_code=404, error_name="not found", error_explanation="the page you are looking for is in another castle."), 404

@app.errorhandler(401)
def page_not_allowed(_):
    return render_template("error.html", error_code=401, error_name="unauthorized", error_explanation="how would you like it if i came into <i>your</i> home and went snooping?"), 404

@app.errorhandler(500)
def page_on_fire(e):
    print("ERROR:", e)
    return render_template("error.html", error_code=500, error_name="internal server error", error_explanation="i broke something really bad. i'm so sorry."), 404

@app.route('/data/assets/<path:path>')
def send_assets(path):
    return send_from_directory('data/assets', path)

# for compatibility with the old rss feed
@app.route('/blog/feed')
def rss_feed_redirect():
    return redirect(url_for('blog.rss_feed'))

@app.route('/sitemap.xml')
def sitemap_redirect():
    return redirect(url_for('blog.sitemap'))


@app.route('/')
def home():  # put application's code here
    global BUTTONS
    if BUTTONS is None:
        BUTTONS = []
        static_buttons = 'static/' + BUTTON_DIRECTORY
        for filename in sorted(os.listdir(static_buttons)):
            if not filename.endswith((".gif", ".png", ".apng", ".jpg")):
                continue

            # Add option for 88x31's to have a link (as they are supposed to)
            link = None
            link_file = static_buttons + "/" + filename + ".txt"
            if os.path.exists(link_file):
                with open(link_file) as file:
                    link = file.read()

            BUTTONS.append({
                "file": url_for('static', filename=BUTTON_DIRECTORY + "/" + filename),
                "link": link
            })

    return render_template("home.html", buttons=BUTTONS, visitors=fetch_all_visitors())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
