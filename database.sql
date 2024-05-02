DROP TABLE IF EXISTS urls;
CREATE TABLE urls (
    id smallint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(255) NOT NULL,
    created_at timestamp NOT NULL
);

INSERT INTO urls (name, created_at) VALUES ('https://www.google.ru', '2011-11-11');
