CREATE TABLE IF NOT EXISTS library (
    id INTEGER PRIMARY KEY,
    path VARCHAR UNIQUE,
    title VARCHAR,
    albumartist VARCHAR,
    artist VARCHAR,
    composer VARCHAR,
    artistsort VARCHAR,
    album VARCHAR,
    bpm INTEGER,
    length INTEGER,
    year INTEGER
);