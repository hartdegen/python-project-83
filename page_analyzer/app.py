from flask import (
    Flask,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    url_for,
)
from dotenv import load_dotenv
from urllib.parse import urlparse
import psycopg2
import psycopg2.extras
import os
import validators

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.secret_key = "secret_key"
DATABASE_URL = os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as c:
        c.execute('SELECT * FROM urls')
except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL")
    print(error)


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template('index.html', messages=messages)


@app.post('/')
def handle_form():
    url = request.form.to_dict()['url']
    is_valid = validators.url(url)
    if is_valid and len(url) < 256:
        o = urlparse(url)
        link = f'{o.scheme}://{o.netloc}'
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
            curs.execute('SELECT * FROM urls WHERE name=%s', (link,))
            url = curs.fetchone()
            if url:
                print('URL ALREADY EXIST')
                flash('Страница уже существует', 'info')
                return redirect(url_for('get_url', id=url['id']))
            curs.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s)", (link, 'now'))  # noqa: E501
            conn.commit()
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('get_urls'))
    if not is_valid:
        flash('Некорректный URL', 'danger')
        return redirect(url_for('index'))


@app.route('/urls/<int:id>')
def get_url(id):
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
        curs.execute('SELECT * FROM urls WHERE id=%s', (id,))
        url = curs.fetchone()
    if url is None:
        return render_template('404.html')
    return render_template('url.html', url=url)


@app.route('/urls')
def get_urls():
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
        curs.execute('SELECT * FROM urls')
        urls = curs.fetchall()
        urls.reverse()
    return render_template('urls.html', urls=urls)


if __name__ == '__main__':
    app.run()
