CREATE TABLE IF NOT EXISTS genre_list (
    library_id INTEGER,
    genre_id INTEGER,
    UNIQUE(library_id, genre_id),
    FOREIGN KEY (library_id) REFERENCES library(id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
);