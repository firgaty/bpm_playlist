WITH RECURSIVE split(string, rest) AS (
    SELECT
        '',
        genre || ';'
    FROM
        import
    UNION
    ALL
    SELECT
        substr(rest, 0, instr(rest, ';')),
        substr(rest, instr(rest, ';') + 1)
    FROM
        split
    WHERE
        rest <> ''
)
INSERT
    OR IGNORE INTO genres(name)
SELECT
    DISTINCT lower(string)
FROM
    split
WHERE
    string <> ''
ORDER BY
    string;