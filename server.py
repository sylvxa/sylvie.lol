import os, time, datetime
import sqlite3
import dotenv
import uuid
from flask import Flask, render_template, url_for, g, request, redirect, send_from_directory
import markdown
app = Flask(__name__)
dotenv.load_dotenv()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

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
    for file in os.listdir("static/" + directory):
        eetos.append(url_for('static', filename=directory + "/" + file))

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
    cursor = get_db().cursor()
    query = SELECT_POSTS_SQL
    cursor.execute(query)
    results = cursor.fetchall()
    posts = list(map(Post.from_db, results)) # Converts each database post to a Python post

    return render_template("blog/explore.html", posts=posts)

@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    cursor = get_db().cursor()
    query = SELECT_POST_BY_ID_SQL
    cursor.execute(query, [post_id])
    result = cursor.fetchone()
    
    return render_template("blog/post.html", post=Post.from_db(result))

@app.route('/blog/supersecretmegacoolendpoint')
def blog_upload():
    return render_template("blog/upload.html")

@app.route('/blog/supersecretmegacoolendpoint/post', methods=['POST'])
def blog_upload_api():
    if request.form.get("password", "") == os.getenv("PASSWORD"):
        title = request.form.get("title", "Untitled")
        description = request.form.get("description", "Undescriptioned")
        content = request.form.get("content", "Uncontented")
        post_id = insert_post(get_db(), title, description, content)

        return redirect(url_for('blog_post', post_id=post_id))
    return "stop poking around, doofus", 401

@app.route('/blog/supersecretmegacoolendpoint/image', methods=['POST'])
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
                return redirect(url_for('static', filename='post-contents/' + filename))

@app.route('/blog/supersecretmegacoolendpoint/delete', methods=['POST'])
def blog_delete_api():
    if request.form.get("password", "") == os.getenv("PASSWORD"):
        post_id = request.form.get("id")
        delete_post(get_db(), post_id)
        return redirect(url_for('blog_explore'))
    return "stop poking around, doofus", 401

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")