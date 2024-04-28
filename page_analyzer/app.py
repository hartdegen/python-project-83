from flask import Flask, render_template
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    secret_key = os.getenv('SECRET_KEY')
    print(11111, secret_key)
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
