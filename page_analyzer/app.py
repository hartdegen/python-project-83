from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def hello():
    secret_key = os.getenv('SECRET_KEY')
    return f'Hello, Flask! Secret Key: {secret_key}'


if __name__ == '__main__':
    app.run()
