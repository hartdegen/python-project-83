DROP TABLE IF EXISTS urls;
DROP TABLE IF EXISTS url_checks;
CREATE TABLE urls (
    id smallint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(255) NOT NULL,
    created_at timestamp NOT NULL
);

CREATE TABLE url_checks (
    id smallint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id smallint NOT NULL,
    status_code smallint,
    h1 varchar(255),
    title varchar(255),
    description text,
    created_at timestamp NOT NULL
);

INSERT INTO urls (name, created_at) VALUES ('https://www.google.ru', '2011-11-11');