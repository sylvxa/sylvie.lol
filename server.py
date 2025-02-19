import datetime
import os
import sqlite3
import time
import uuid
from typing import Optional

import requests
from xml.dom import minidom

from email.utils import format_datetime

import dotenv
import markdown
from flask import Flask, render_template, url_for, g, request, redirect, send_from_directory, Response

app = Flask(__name__)
dotenv.load_dotenv()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


ROOT_PAGE = "https://sylvie.lol"
ABOUT_ME = "static/pages/home.md"

with open(ABOUT_ME, "r", encoding="utf-8") as f:
    HOME_TEXT = markdown.markdown(f.read())

FIRST_POST = "static/pages/hello.md"
DATABASE = "blog.db"

CREATE_TABLE_SQL = "CREATE TABLE blog ( \
    id INTEGER PRIMARY KEY, \
    title text, \
    description text, \
    content text, \
    posted TIMESTAMP)"
INSERT_POST_SQL = "INSERT INTO blog (id, title, description, content, posted) VALUES (?,?,?,?,DATETIME())"
SELECT_POSTS_SQL = "SELECT * FROM blog ORDER BY id DESC;"  # The "id"s are really just unix timestamps
SELECT_POST_BY_ID_SQL = "SELECT * FROM blog WHERE id = ?"
DELETE_POST_BY_ID_SQL = "DELETE FROM blog WHERE id = ?"


def initialize_db():
    db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = db.cursor()
    try:
        cursor.execute(CREATE_TABLE_SQL)
        with open(FIRST_POST, "r", encoding="utf-8") as post_file:
            cursor.execute(INSERT_POST_SQL,
                           [int(time.time()),
                            "Hello world!",
                            "This is my site, welcome!",
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


@app.teardown_appcontext
def close_connection(_):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


LAST_FETCHED = datetime.datetime(1970, 1, 1)  # Make sure it gets fetched if we reboot
PROFILE_URL_FORMAT = "https://discord.com/api/v10/users/{id}"
IMAGE_URL_FORMAT = "https://cdn.discordapp.com/avatars/{id}/{avatar}.png?size=128"
IMAGE_LOCATION = "static/assets/discord-profile.png"
discord_username = "sylvie <3"


def get_discord_profile() -> str:
    global discord_username, LAST_FETCHED

    # Use cached values if it's been more than 3 days since the last time it was fetched.
    delta = datetime.datetime.now() - LAST_FETCHED
    if delta.days <= 3:
        return discord_username

    # Make a request using a Discord bot to get my user profile
    discord_id = os.getenv("DISCORD_ID")
    profile_request = requests.get(PROFILE_URL_FORMAT.replace("{id}", discord_id), headers={
        "Authorization": "Bot " + os.getenv("DISCORD_TOKEN"),
        "User-Agent": "DiscordBot (https://sylvie.lol/, 1.0.0)"
    })

    if profile_request.ok:
        profile = profile_request.json()
        discord_username = profile.get('global_name', discord_username)

        # We download the image to avoid spamming Discord's CDN too much.
        image_url = (IMAGE_URL_FORMAT
                     .replace("{id}", discord_id)
                     .replace("{avatar}", profile.get("avatar")))
        image_request = requests.get(image_url)
        if image_request.ok:
            image = image_request.content

            with open(IMAGE_LOCATION, 'wb') as image_file:
                image_file.write(image)
        else:
            print("Couldn't fetch Discord profile picture!")
            print(image_request.text)
    else:
        print("Couldn't fetch Discord profile!")
        print(profile_request.text)

    LAST_FETCHED = datetime.datetime.now()
    return discord_username


UTC_OFFSET = -5


@app.route('/')
def home():
    # Make info card reflect my Discord profile
    discord_name = get_discord_profile()

    # Get timezone info for people who don't use JavaScript
    #utc_now = datetime.datetime.now(datetime.timezone.utc)
    #timezone = datetime.timezone(datetime.timedelta(hours=UTC_OFFSET))

    #offset_now = utc_now.astimezone(timezone)
    #formatted_now = offset_now.strftime("%I:%M %p")

    return render_template("home.html",
                           home_text=HOME_TEXT,  # Markdown formatted home text
                           discord_name=discord_name)  # Time formatted


@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/buttons')
def buttons():
    # Append 88x31s
    eetos = []  # (E)ight(E)ight(T)hree(O)nes
    directory = "assets/eighteightthreeone"
    for filename in sorted(os.listdir("static/" + directory)):
        filename = directory + "/" + filename
        if not filename.endswith((".gif", ".png", ".apng", ".jpg")):
            continue

        # Add option for 88x31's to have a link (as they are supposed to)
        link = None
        link_file = "static/" + filename + ".txt"
        if os.path.exists(link_file):
            with open(link_file) as file:
                link = file.read()

        eetos.append({
            "file": url_for('static', filename=filename),
            "link": link
        })

    return render_template("buttons.html", eeto=eetos)

class Post:
    def __init__(self, post_id: int, title: str, description: str, content: str, posted: datetime.datetime) -> None:
        self.post_id = post_id
        self.title = title
        self.description = description
        self.content = content
        self.posted = posted

    @staticmethod
    def from_db(obj: tuple):
        return Post(*obj)  # Database objects are laid out in the same way the arguments are, so we can "unpack" them

    def format_timestamp(self) -> str:
        return self.posted.strftime("%B %d, %Y").upper()

    def markdown_content(self) -> str:
        return markdown.markdown(self.content)

    def get_url(self) -> str:
        return url_for("blog_post", post_id=self.post_id)


def fetch_all_posts() -> list[Post]:
    cursor = get_db().cursor()
    query = SELECT_POSTS_SQL
    cursor.execute(query)
    results = cursor.fetchall()
    return list(map(Post.from_db, results))


def insert_post(db, title: str, description: str, content: str) -> int:
    post_id = int(time.time())
    cursor = db.cursor()
    cursor.execute(INSERT_POST_SQL, [post_id, title, description, content])
    db.commit()
    return post_id


def delete_post(db, post_id: str):
    cursor = db.cursor()
    cursor.execute(DELETE_POST_BY_ID_SQL, [post_id])
    db.commit()


@app.route('/blog')
def blog():
    return render_template("blog/explore.html", posts=fetch_all_posts())


@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    cursor = get_db().cursor()
    query = SELECT_POST_BY_ID_SQL
    cursor.execute(query, [post_id])
    result = cursor.fetchone()
    if not result:
        return render_template("not_found.html"), 404
    return render_template("blog/post.html", post=Post.from_db(result))


# Sitemap
def xml_text_obj(document: minidom.Document, name: str, value: any):
    element = document.createElement(name)
    text_node = document.createTextNode(str(value))
    element.appendChild(text_node)
    return element


def xml_url_obj(document: minidom.Document,
                location: str,
                last_modified: Optional[datetime.datetime],
                change_frequency: str,
                priority: float):
    url = document.createElement('url')
    url.appendChild(xml_text_obj(document, "loc", location))
    if last_modified is not None:
        url.appendChild(xml_text_obj(document, "lastmod", last_modified.strftime("%Y-%m-%d")))
    if change_frequency is not None:
        url.appendChild(xml_text_obj(document, "changefreq", change_frequency))
    if priority is not None:
        url.appendChild(xml_text_obj(document, "priority", priority))
    return url

# Sitemap
@app.route('/sitemap.xml')
def sitemap():
    document = minidom.Document()
    urlset = document.createElement('urlset')
    urlset.setAttribute("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    urlset.appendChild(xml_url_obj(document, ROOT_PAGE, None, "monthly", 1.0))
    urlset.appendChild(xml_url_obj(document, ROOT_PAGE + "/blog", None, "monthly", 0.9))

    for post in fetch_all_posts():
        urlset.appendChild(xml_url_obj(document, ROOT_PAGE + post.get_url(), post.posted, "yearly", 0.7))

    document.appendChild(urlset)
    content = document.toprettyxml(indent="\t")
    return Response(content, mimetype='text/xml')


# RSS
@app.route('/blog/feed')
def rss_feed():
    document = minidom.Document()

    root = document.createElement('rss')
    root.setAttribute("version", "2.0")
    root.setAttribute("xmlns:atom", "http://www.w3.org/2005/Atom")

    channel = document.createElement('channel')
    
    # Channel attributes
    channel.appendChild(xml_text_obj(document, "title", "Sylvie's Blog"))
    channel.appendChild(xml_text_obj(document, "link", "https://sylvie.lol/blog"))
    channel.appendChild(xml_text_obj(document, "description", "Some writeups on what I've been working on."))

    channel.appendChild(xml_text_obj(document, "language", "en-us"))

    who_i_am = "sylvia@sylvie.lol (Sylvie <3)"
    channel.appendChild(xml_text_obj(document, "managingEditor", who_i_am))
    channel.appendChild(xml_text_obj(document, "webMaster", who_i_am))

    channel.appendChild(xml_text_obj(document, "generator", "Sylvie's Super-Duper Cool RSS Feed Generator"))

    # atom:link
    atom_link = document.createElement("atom:link")
    atom_link.setAttribute("href", ROOT_PAGE + url_for("rss_feed"))
    atom_link.setAttribute("rel", "self")
    atom_link.setAttribute("type", "application/rss+xml")
    channel.appendChild(atom_link)

    # Posts
    for post in fetch_all_posts():
        item = document.createElement("item")

        absolute_url = ROOT_PAGE + post.get_url()
        item.appendChild(xml_text_obj(document, "title", post.title))
        item.appendChild(xml_text_obj(document, "link", absolute_url))
        item.appendChild(xml_text_obj(document, "description", post.description))

        item.appendChild(xml_text_obj(document, "guid", absolute_url))

        item.appendChild(xml_text_obj(document, "pubDate", format_datetime(post.posted)))

        channel.appendChild(item)


    root.appendChild(channel)
    document.appendChild(root)

    content = document.toprettyxml(indent="\t")    
    return Response(content, mimetype='text/xml')


# Blog control
@app.route('/blog/control')
def blog_upload():
    return render_template("blog/upload.html")


@app.route('/blog/control/post', methods=['POST'])
def blog_upload_api():
    if request.form.get("password", "") == os.getenv("PASSWORD"):
        title = request.form.get("title", "Untitled")
        description = request.form.get("description", "Undescriptioned")
        content = request.form.get("content", "Uncontented")
        post_id = insert_post(get_db(), title, description, content)

        return redirect(url_for('blog_post', post_id=post_id))
    return "Could you stop poking around? Thank you!", 401


@app.route('/blog/control/image', methods=['POST'])
def blog_upload_image_api():
    if request.form.get("password", "") == os.getenv("PASSWORD"):
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '':
                filename = str(uuid.uuid4()) + "." + file.filename.rsplit('.', 1)[1].lower()
                folder_path = f"static/post-contents"
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                file.save(os.path.join(folder_path, filename))
                return url_for('static', filename='post-contents/' + filename)
            else:
                return "Filename is empty"
        else:
            return "No file found"
    else:
        return "Get your own image service!", 401


@app.route('/blog/control/delete', methods=['POST'])
def blog_delete_api():
    if request.form.get("password", "") == os.getenv("PASSWORD"):
        post_id = request.form.get("id")
        delete_post(get_db(), post_id)
        return redirect(url_for('blog_explore'))
    return "Hey, get outta there!", 401


@app.errorhandler(404)
def not_found(e):
    return render_template("not_found.html"), 404


@app.errorhandler(500)
def error(e):
    return render_template("borked.html"), 500


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
