WITH t AS (
    SELECT
        DISTINCT import.path,
        import.title,
        import.albumartist,
        import.artist,
        import.composer,
        import.album,
        import.bpm,
        import.length,
        import.year
    from
        import
)
INSERT
    OR IGNORE INTO library(
        path,
        title,
        albumartist,
        artist,
        composer,
        album,
        bpm,
        length,
        year
    )
SELECT
    *
from
    t