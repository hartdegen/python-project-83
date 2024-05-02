install:
	poetry install

lint:
	poetry run flake8 page_analyzer

build:
	./build.sh

dev:
	# poetry run flask --app page_analyzer:app run
	poetry run flask --app page_analyzer:app --debug run

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

