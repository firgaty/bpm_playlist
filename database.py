import sqlite3
import os
import pathlib
import sys
from query import Query, QueryColumn

from xdg import xdg_config_home
from typing import Iterator
from user_types import MetaDict, MetaValue

path = pathlib.Path(os.path.abspath(os.path.dirname(sys.argv[0])))
sql_path = path.joinpath("sql")
db_dir = pathlib.Path(xdg_config_home()).joinpath("daifukusan", "bpm_playlist")
db_path = db_dir.joinpath("database.db")
db_dir.mkdir(parents=True, exist_ok=True)


class __Database:
    __db_columns = [
        "path",
        "title",
        "albumartist",
        "artist",
        "composer",
        "genre",
        "artistsort",
        "album",
        "bpm",
        "length",
        "year",
    ]

    def __init__(self):
        self.__conn = sqlite3.connect(db_path)
        self.__c = self.__conn.cursor()
        self.__queries = None

        if self.__queries is None:
            self.__queries = {}
            path = pathlib.Path(os.path.abspath(os.path.dirname(sys.argv[0]))).joinpath(
                "sql"
            )

            for p in self.__walk_path(path):
                with open(p) as f:
                    self.__queries[self.__path_to_func(path, p)] = f.read()

        self.__init()

    def __walk_path(
        self, path: str, file_extentions: list[str] = [".sql"]
    ) -> Iterator[str]:
        for (dirpath, _, filenames) in os.walk(path):
            for filename in filenames:
                for ext in file_extentions:
                    if filename.endswith(ext):
                        yield os.path.join(dirpath, filename)
                        break

    def __path_to_func(self, root: str, path: str, ext: str = ".sql") -> str:
        p = os.path.relpath(path, root)
        p = p.replace(".sql", "").replace("/", ".")
        return p

    def __init(self) -> None:
        self.__c.execute(self.__queries["create.library"])
        self.__c.execute(self.__queries["create.genres"])
        self.__c.execute(self.__queries["create.import"])
        self.__c.execute(self.__queries["create.genre_list"])
        self.__c.execute(self.__queries["create.genres_concat_view"])
        self.__conn.commit()

    def add_entries(self, entries: list[MetaDict]) -> None:
        self.__c.executemany(
            self.__queries["insert.import"], self.__meta_dict_values_iter(entries)
        )
        self.__conn.commit()

    def commit_import(self) -> None:
        self.__c.execute(self.__queries["function.import.to_library"])
        self.__c.execute(self.__queries["function.import.to_genres"])
        self.__c.execute(self.__queries["function.import.to_genre_list"])
        self.__conn.commit()
        self.__c.execute(self.__queries["truncate.import"])
        self.__conn.commit()

    def __meta_dict_values_iter(
        self, meta_dicts: list[MetaDict]
    ) -> Iterator[list[MetaValue]]:
        for d in meta_dicts:
            yield self.__meta_dict_values(d)

    def __meta_dict_values(self, meta_dict: MetaDict) -> list[MetaValue]:
        meta = []
        for field in self.__db_columns:
            meta.append(meta_dict[field])
        return meta

    def path_exists(self, path: str) -> bool:
        return (
            len(
                self.__c.execute(
                    self.__queries["query.path_exists"], (path,)
                ).fetchall()
            )
            > 0
        )

    def count_entries(self) -> int:
        return self.__c.execute(self.__queries["query.count_entries"]).fetchone()

    def paths(self) -> list[str]:
        return self.__c.execute("SELECT path FROM library").fetchall()

    def delete_entry(self, col_id: int = None, path: str = None) -> None:
        if col_id is not None:
            self.__c.execute("DELETE FROM library WHERE id = ?", col_id)
        elif path is not None:
            self.__c.execute("DELETE FROM library WHERE path = ?", path)

    def query(self, query: Query) -> dict:
        q, args, cols = query.to_query()

        f = self.__c.execute(q, args).fetchall()
        elements = []
        for e in f:
            d = {}

            for i in range(len(cols)):
                d[cols[i][0]] = e[i]

            elements.append(d)

        return elements

    def column(self, column: QueryColumn, limit: int = -1):
        q = f"SELECT DISTINCT {column.real_name()} FROM {column.table}"
        q += f"\nORDER BY {column.original_name()}"

        if limit > 0:
            q += f" LIMIT {limit}"

        r = self.__c.execute(q).fetchall()

        return [e[0] for e in r]


DB = __Database()
