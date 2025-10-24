import time
from email.utils import format_datetime
from typing import Optional
from xml.dom import minidom

import markdown
from flask import Blueprint, abort, render_template, url_for, Response
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

# Sitemap
ROOT_PAGE = "https://sylvie.lol"

def xml_text_obj(document: minidom.Document, name: str, value: any):
    element = document.createElement(name)
    text_node = document.createTextNode(str(value))
    element.appendChild(text_node)
    return element


def xml_url_obj(document: minidom.Document,
                location: str,
                last_modified: Optional[datetime],
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

@blog.route('/sitemap.xml')
def sitemap():
    document = minidom.Document()
    urlset = document.createElement('urlset')
    urlset.setAttribute("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    urlset.appendChild(xml_url_obj(document, ROOT_PAGE, None, "monthly", 1.0))
    urlset.appendChild(xml_url_obj(document, ROOT_PAGE + "/journal", None, "monthly", 0.9))

    for post in fetch_all_posts():
        urlset.appendChild(xml_url_obj(document, ROOT_PAGE + url_for("blog.view", post_id=post[0]), post[5], "yearly", 0.7))

    document.appendChild(urlset)
    content = document.toprettyxml(indent="\t")
    return Response(content, mimetype='text/xml')


# RSS
@blog.route('/feed')
def rss_feed():
    document = minidom.Document()

    root = document.createElement('rss')
    root.setAttribute("version", "2.0")
    root.setAttribute("xmlns:atom", "http://www.w3.org/2005/Atom")

    channel = document.createElement('channel')

    # Channel attributes
    channel.appendChild(xml_text_obj(document, "title", "sylvie's journal"))
    channel.appendChild(xml_text_obj(document, "link", "https://sylvie.lol/blog"))
    channel.appendChild(xml_text_obj(document, "description", "what i've been up to, and other ramblings"))

    channel.appendChild(xml_text_obj(document, "language", "en-us"))

    who_i_am = "me@sylvie.lol (sylvie <3)"
    channel.appendChild(xml_text_obj(document, "managingEditor", who_i_am))
    channel.appendChild(xml_text_obj(document, "webMaster", who_i_am))

    channel.appendChild(xml_text_obj(document, "generator", "sylvie's super-duper cool RSS feed generator ultra deluxe"))

    # atom:link
    atom_link = document.createElement("atom:link")
    atom_link.setAttribute("href", ROOT_PAGE + url_for("blog.rss_feed"))
    atom_link.setAttribute("rel", "self")
    atom_link.setAttribute("type", "application/rss+xml")
    channel.appendChild(atom_link)

    # Posts
    for post in fetch_all_posts():
        item = document.createElement("item")

        absolute_url = ROOT_PAGE + url_for("blog.view", post_id=post[0])
        item.appendChild(xml_text_obj(document, "title", post[2]))
        item.appendChild(xml_text_obj(document, "link", absolute_url))
        item.appendChild(xml_text_obj(document, "description", post[3]))

        item.appendChild(xml_text_obj(document, "guid", absolute_url))

        item.appendChild(xml_text_obj(document, "pubDate", format_datetime(post[5])))

        channel.appendChild(item)

    root.appendChild(channel)
    document.appendChild(root)

    content = document.toprettyxml(indent="\t")
    return Response(content, mimetype='text/xml')