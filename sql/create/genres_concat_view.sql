CREATE VIEW IF NOT EXISTS genres_concat_view AS
SELECT
    genre_list.library_id AS library_id,
    GROUP_CONCAT(genres.name, ';') AS genres
FROM
    genre_list
    JOIN genres ON genre_list.genre_id = genres.id
GROUP BY
    library_id;
