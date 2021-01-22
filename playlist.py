import os
import random
from database import DB
from query import (
    Query,
    QueryNotInOption,
    ColumnType,
    QueryColumn,
    QueryInOption,
    QueryBetweenOption,
    QueryInfToOption,
    QuerySupToOption,
)


def sec_to_min(sec: int) -> str:
    s = sec % 60
    m = sec // 60

    return f"{m}:{s:02}"


def sec_to_hour(sec: int) -> str:
    s = sec % 60
    m = sec // 60
    h = m // 60
    m = m % 60

    return f"{h}:{m:02}:{s:02}"


class Track:
    def __init__(
        self,
        id: str = "",
        path: str = "",
        title: str = "",
        albumartist: str = "",
        artist: str = "",
        composer: str = "",
        artistsort: str = "",
        album: str = "",
        genres: str = "",
        bpm: int = 0,
        length: int = 0,
    ):
        self.id = id
        self.path = path
        self.title = title
        self.albumartist = albumartist
        self.artist = artist
        self.composer = composer
        self.artistsort = artistsort
        self.album = album
        self.genres = genres
        self.bpm = bpm
        self.length = length
        self.dict = {
            "id": self.get_id,
            "path": self.get_path,
            "title": self.get_title,
            "albumartist": self.get_albumartist,
            "artist": self.get_artist,
            "composer": self.get_composer,
            "artistsort": self.get_artistsort,
            "album": self.get_album,
            "bpm": self.get_bpm,
            "length": self.get_length,
        }

    def __hash__(self):
        return hash((self.title, self.albumartist))

    def __eq__(self, other):
        return self.title == other.title and self.albumartist == other.albumartist

    def __repr__(self) -> str:
        return (
            f"{self.title} - {self.albumartist} - {self.album}"
            + f" - {self.bpm} - {sec_to_min(self.length)}"
        )

    def to_m3u(self, root_path: str = "") -> str:
        p = self.path if root_path == "" else os.path.relpath(self.path, root_path)
        return f"#EXTINF:{self.length},{self.albumartist} - {self.title}\n" + f"{p}"

    def get(self, member: str):
        return self.dict[member]()

    def get_id(self) -> str:
        return self.id

    def get_path(self) -> str:
        return self.path

    def get_title(self) -> str:
        return self.title

    def get_albumartist(self) -> str:
        return self.albumartist

    def get_artist(self) -> str:
        return self.artist

    def get_composer(self) -> str:
        return self.composer

    def get_artistsort(self) -> str:
        return self.artistsort

    def get_album(self) -> str:
        return self.album

    def get_genres(self) -> str:
        return self.genres

    def get_bpm(self) -> int:
        return self.bpm

    def get_length(self) -> int:
        return self.length


class Playlist:
    def __init__(self, title: str = "", root_path: str = ""):
        self.title: str = title
        self.root_path: str = root_path
        self.tracks: list[Track] = []

    def add_track(self, track: Track) -> None:
        self.tracks.append(track)

    def to_m3u(self) -> str:
        s = "#EXTM3U\n"

        for t in self.tracks:
            s += t.to_m3u(self.root_path) + "\n"

        return s

    def sort(self, keys: list[str] = []) -> None:
        def k(track: Track):
            return tuple([track.get(field) for field in keys])

        self.tracks.sort(key=lambda t: k(t))

    def remove_duplicates(self):
        self.tracks = list(set(self.tracks))

    def shuffle(self) -> None:
        random.shuffle(self.tracks)

    def __repr__(self) -> str:
        # s = f"{self.title}:\n"
        s = ""
        time = 0
        i = 0

        n = len(str(len(self.tracks)))

        for t in self.tracks:
            i += 1
            s += f"{i:>{n}}| " + str(t) + "\n"
            time += t.length

        if self.title != "":
            s = self.title + ": \n" + s

        s += f"\n{sec_to_hour(time)} : {i}"
        return s

    def limit_time(self, minutes: int) -> None:

        self.shuffle()

        W = minutes * 60
        t = 0
        i = 0

        while t < W and i < len(self.tracks):
            t += self.tracks[i].length
            i += 1

        self.tracks = self.tracks[:i]

        while True:
            for e in self.tracks:
                if e.length < t - W:
                    self.tracks.remove(e)
                    t -= e.length
                    break
            else:
                break


class Creator:
    def __init__(self):
        self.query = Query(
            columns=[
                QueryColumn("id", ColumnType.STR, "library", "id"),
                QueryColumn("path", ColumnType.STR, "library", "path"),
                QueryColumn("title", ColumnType.STR, "library", "title"),
                QueryColumn("albumartist", ColumnType.STR, "library", "albumartist"),
                QueryColumn("artist", ColumnType.STR, "library", "artist"),
                QueryColumn("composer", ColumnType.STR, "library", "composer"),
                QueryColumn("artistsort", ColumnType.STR, "library", "artistsort"),
                QueryColumn("album", ColumnType.STR, "library", "album"),
                QueryColumn(
                    "GROUP_CONCAT(genres.name, ';')", ColumnType.STR, alias="genres"
                ),
                QueryColumn("bpm", ColumnType.INT, "library", "bpm"),
                QueryColumn("length", ColumnType.INT, "library", "length"),
            ],
            group_by=[
                QueryColumn("id", ColumnType.STR, "library", "id"),
            ],
        )

        self.query.add_table("genres")

        self.length = -1
        self.title = ""
        self.root_path = ""

    def generate_playlist(self) -> Playlist:
        p = Playlist(self.title, self.root_path)

        for args in DB.query(self.query):
            p.add_track(Track(**args))

        p.remove_duplicates()

        if self.length > 0:
            p.limit_time(self.length)

        return p

    def with_number_of_tracks(self, n: int):
        self.query.limit = n
        return self

    def with_bpm_bounds(self, minimum: int, maximum: int):
        self.query.add_option(QueryBetweenOption("library", "bpm", minimum, maximum))
        return self

    def with_bpm_upper_bound(self, bound: int):
        self.query.add_option(QueryInfToOption("library", "bpm", bound))
        return self

    def with_bpm_lower_bound(self, bound: int):
        self.query.add_option(QuerySupToOption("library", "bpm", bound))
        return self

    def with_length_upper_bound(self, bound: int):
        self.query.add_option(QueryInfToOption("library", "length", bound))
        return self

    def with_length_lower_bound(self, bound: int):
        self.query.add_option(QuerySupToOption("library", "length", bound))
        return self

    def with_artist_restrict(self, artists: list[str]):
        self.query.add_option(QueryInOption("library", "albumartist", artists))
        return self

    def with_artist_exclude(self, artists: list[str]):
        self.query.add_option(QueryNotInOption("library", "albumartist", artists))
        return self

    def with_genres_restrict(self, genres: list[str]):
        self.query.add_option(QueryInOption("genres", "name", genres))
        return self

    def with_genres_exclude(self, genres: list[str]):
        self.query.add_option(QueryNotInOption("genres", "name", genres))
        return self

    def with_random(self):
        self.query.order_by_random = True
        return self

    def with_length(self, length: int):
        self.length = length
        return self

    def with_root(self, root: str):
        self.root_path = root
        return self
