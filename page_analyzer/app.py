from datetime import date
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse
from psycopg2.extras import NamedTupleCursor
import psycopg2
import requests
import validators
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "secret_key"
DATABASE_URL = os.getenv("DATABASE_URL")


try:
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=3)
except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL")
    print(error)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/urls/<int:id>")
def get_url(id):
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=3)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute("SELECT * FROM urls WHERE id=%s", (id,))
        url = curs.fetchone()
        curs.execute("SELECT * FROM url_checks WHERE url_id=%s", (id,))
        url_checks = curs.fetchall()
        url_checks.reverse()
    if url is None:
        return render_template("404.html")
    return render_template("url.html", url=url, url_checks=url_checks)


@app.post("/urls/<int:id>/checks")
def check_url(id):
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=3)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute("SELECT * FROM urls WHERE id=%s", (id,))
        url = str(curs.fetchone().name)
        try:
            r = requests.get(url, timeout=3)
            r.raise_for_status()
            status_code = r.status_code
            soup = BeautifulSoup(r.content, 'html.parser')
            h1 = soup.select("h1")[0].string if len(soup.select("h1")) > 0 else ''  # noqa: E501
            title = soup.select("title")[0].string if len(soup.select("title")) > 0 else ''  # noqa: E501
            description = soup.select('meta[name="description"]')[0]['content'] if len(soup.select('meta[name="description"]')) > 0 else ''  # noqa: E501
            curs.execute("""
            INSERT INTO url_checks
            (url_id, status_code, created_at, h1, title, description)
            VALUES
            (%s, %s, %s, %s, %s, %s)
            """, (id, status_code, str(date.today()), h1, title, description),)
            conn.commit()
        except requests.exceptions.RequestException as e:
            print('ERROR def check_url(id)')
            print(e)
            flash("Произошла ошибка при проверке", "danger")
            return redirect(url_for("get_url", id=id))
    flash("Страница успешно проверена", "success")
    return redirect(url_for("get_url", id=id))


@app.route("/urls", methods=['GET', 'POST'])
def get_urls():
    if request.method == "GET":
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=3)
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute("""
            SELECT
                urls.id,
                urls.name,
                MAX(url_checks.created_at) AS last_check,
                MAX(url_checks.status_code) AS status_code
            FROM urls
            LEFT JOIN url_checks
                ON urls.id = url_checks.url_id
            GROUP BY urls.id
            ORDER BY urls.id DESC
            """)
            urls = curs.fetchall()
        return render_template("urls.html", urls=urls)
    if request.method == "POST":
        url = request.form.get('url')
        is_valid = validators.url(url)
        if is_valid and len(url) < 256:
            o = urlparse(url)
            link = f"{o.scheme}://{o.netloc}"
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=3)
            with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
                curs.execute("SELECT * FROM urls WHERE name=%s", (link,))
                url = curs.fetchone()
                if url:
                    flash("Страница уже существует", "info")
                    return redirect(url_for("get_url", id=url.id))
                curs.execute("""
                INSERT INTO urls (name, created_at)
                VALUES (%s, %s)
                """, (link, str(date.today())),)
                conn.commit()
                curs.execute("SELECT id FROM urls WHERE name=%s", (link,))
                id = curs.fetchone().id
                flash("Страница успешно добавлена", "success")
                return redirect(url_for("get_url", id=id))
        if not is_valid:
            flash("Некорректный URL", "danger")
            return render_template('index.html'), 422


if __name__ == "__main__":
    app.run()
