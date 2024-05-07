from datetime import date
from flask import (
    Flask,
    flash,
    get_flashed_messages,
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
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.secret_key = "secret_key"
DATABASE_URL = os.getenv("DATABASE_URL")


try:
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as c:
        c.execute("SELECT * FROM urls")
except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL")
    print(error)


@app.route("/")
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.post("/")
def handle_form():
    url = request.form.get('url')
    is_valid = validators.url(url)
    if is_valid and len(url) < 256:
        o = urlparse(url)
        link = f"{o.scheme}://{o.netloc}"
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
        return redirect(url_for("index"))


@app.route("/urls/<int:id>")
def get_url(id):
    messages = get_flashed_messages(with_categories=True)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute("SELECT * FROM urls WHERE id=%s", (id,))
        url = curs.fetchone()
        curs.execute("SELECT * FROM url_checks WHERE url_id=%s", (id,))
        url_checks = curs.fetchall()
        url_checks.reverse()
    if url is None:
        return render_template("404.html")
    return render_template(
        "url.html", url=url, url_checks=url_checks, messages=messages
    )


@app.post("/urls/<int:id>/checks")
def check_url(id):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute("SELECT * FROM urls WHERE id=%s", (id,))
        url = str(curs.fetchone().name)
        try:
            r = requests.get(url, timeout=1)
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


@app.route("/urls")
def get_urls():
    messages = get_flashed_messages(with_categories=True)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute("""
        WITH u AS (
            SELECT
                urls.id,
                urls.name,
                MAX(url_checks.created_at) AS last_check
            FROM urls
            LEFT JOIN url_checks
                ON urls.id = url_checks.url_id
            GROUP BY urls.id
        )

        SELECT
            u.id,
            u.name,
            u.last_check,
            url_checks.status_code
        FROM u
        LEFT JOIN url_checks
            ON u.last_check = url_checks.created_at
        GROUP BY u.id, u.name, u.last_check, url_checks.status_code
        ORDER BY u.id DESC
        """)
        urls = curs.fetchall()
    return render_template("urls.html", urls=urls, messages=messages)


if __name__ == "__main__":
    app.run()
