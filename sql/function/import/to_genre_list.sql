WITH RECURSIVE split(title, album, albumartist, genre, rest) AS (
    SELECT
        import.title,
        import.album,
        import.albumartist,
        '',
        import.genre || ';'
    FROM
        import AS import
    UNION
    ALL
    SELECT
        title,
        album,
        albumartist,
        substr(rest, 0, instr(rest, ';')),
        substr(rest, instr(rest, ';') + 1)
    FROM
        split
    WHERE
        rest <> ''
),
split_res AS (
    SELECT
        title,
        album,
        albumartist,
        lower(genre) AS genre
    from
        split
    where
        genre <> ''
)
INSERT
    OR IGNORE INTO genre_list(library_id, genre_id)
SELECT
    DISTINCT library.id AS model_id,
    genres.id AS tag_id
FROM
    import
    JOIN library ON library.path = import.path
    JOIN split_res ON split_res.title = import.title
    AND split_res.album = import.album
    AND split_res.albumartist = import.albumartist
    JOIN genres ON genres.name = split_res.genre