import os, time, datetime
import sqlite3
import dotenv
import uuid
from flask import Flask, render_template, url_for, g, request, redirect, send_from_directory, Response
from xml.dom import minidom
import markdown
app = Flask(__name__)
dotenv.load_dotenv()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

ROOT_PAGE = "https://sylvie.lol"
ABOUT_ME = "static/pages/home.md"
FIRST_POST = "static/pages/hello.md"
DATABASE = "blog.db"

CREATE_TABLE_SQL = "CREATE TABLE blog ( \
    id INTEGER PRIMARY KEY, \
    title text, \
    description text, \
    content text, \
    posted TIMESTAMP)"
INSERT_POST_SQL = "INSERT INTO blog (id, title, description, content, posted) VALUES (?,?,?,?,DATETIME())"
SELECT_POSTS_SQL = "SELECT * FROM blog ORDER BY id DESC;" # The "id"s are really just unix timestamps
SELECT_POST_BY_ID_SQL = "SELECT * FROM blog WHERE id = ?"
DELETE_POST_BY_ID_SQL = "DELETE FROM blog WHERE id = ?"

def initialize_db():
    db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = db.cursor()
    try:
        cursor.execute(CREATE_TABLE_SQL)
        with open(FIRST_POST, "r", encoding="utf-8") as f:
            cursor.execute(INSERT_POST_SQL, [int(time.time()), "Hello world!", "This is my site, welcome!", f.read()])
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
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    # The "about me" text.
    home_text = None
    with open(ABOUT_ME, "r", encoding="utf-8") as f:
        content = f.read()
        home_text = markdown.markdown(content)

    # Append 88x31s
    eetos = [] # (E)ight(E)ight(T)hree(O)nes
    directory = "assets/eighteightthreeone"
    for file in sorted(os.listdir("static/" + directory)):
        filename = directory + "/" + file
        if not filename.endswith(".gif") and not filename.endswith(".png") and not filename.endswith(".jpg"): continue
        
        # Add option for 88x31's to have a link (as they are supposed to)
        link = "#"
        link_file = "static/" + filename + ".txt"
        if os.path.exists(link_file):
            with open(link_file) as file:
                link = file.read()

        eetos.append({
            "file": url_for('static', filename=filename),
            "link": link
        })

    return render_template("home.html", eeto=eetos, home_text=home_text)

@app.route('/contact')
def contact():
    return render_template("contact.html")

class Post:
    def __init__(self, id: int, title: str, description: str, content: str, posted: datetime.datetime) -> None:
        self.id = id
        self.title = title
        self.description = description
        self.content = content
        self.posted = posted

    @staticmethod
    def from_db(obj: tuple):
        return Post(*obj) # Database objects are layed out in the same way the arguments are, so we can just "unpack" them
    
    def format_timestamp(self) -> str:
        return self.posted.strftime("%B %d, %Y").upper()
    
    def markdown_content(self) -> str:
        return markdown.markdown(self.content)
    
    def get_url(self) -> str:
        return url_for("blog_post", post_id=self.id)

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

def delete_post(db, post_id: str) -> int:
    cursor = db.cursor()
    cursor.execute(DELETE_POST_BY_ID_SQL, [post_id])
    db.commit()
    return post_id

@app.route('/blog')
def blog_explore():
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

def xml_text_obj(document: minidom.Document, name: str, value: any):
    element = document.createElement(name)
    text_node = document.createTextNode(str(value))
    element.appendChild(text_node)
    return element

def xml_url_obj(document: minidom.Document, location: str, last_modified: datetime.datetime, change_frequency: str, priority: float):
    url = document.createElement('url') 
    url.appendChild(xml_text_obj(document, "loc", location))
    if last_modified is not None:
        url.appendChild(xml_text_obj(document, "lastmod", last_modified.strftime("%Y-%m-%d")))
    if change_frequency is not None:
        url.appendChild(xml_text_obj(document, "changefreq", change_frequency))
    if priority is not None:
        url.appendChild(xml_text_obj(document, "priority", priority))
    return url

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
    content = document.toprettyxml(indent = "\t")  
    return Response(content, mimetype='text/xml')

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
    return "stop poking around, doofus", 401

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
        return "get out ya nosy prick", 401

@app.route('/blog/control/delete', methods=['POST'])
def blog_delete_api():
    if request.form.get("password", "") == os.getenv("PASSWORD"):
        post_id = request.form.get("id")
        delete_post(get_db(), post_id)
        return redirect(url_for('blog_explore'))
    return "stop poking around, doofus", 401

@app.errorhandler(404) 
def not_found(e): 
    return render_template("not_found.html") 

@app.errorhandler(500)
def error(e): 
    return render_template("borked.html") 

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")