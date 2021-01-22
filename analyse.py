import os
import re
import subprocess
import pathlib
from typing import Iterator

from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC

from database import DB
from user_types import MetaDict
from awesome_progress_bar import ProgressBar


bpm_pattern = re.compile(r"(\d+|\d+\.\d+) BPM$")
time_pattern = re.compile(r"(\d+\.\d+)")


def extract_pattern(output: str, pattern) -> int:
    """Transforms a string representing a float to an int."""
    match = pattern.search(output)

    try:
        if match:
            return round(float(match.group(1)))
    except ValueError:
        raise ValueError()
    return 0


def extract_bpm(path: str) -> str:
    """Executes `bpm-tag` program to extract BPM information."""
    out = subprocess.Popen(
        [
            "bpm-tag",
            "-n",
            path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, _ = out.communicate()
    try:
        return extract_pattern(stdout.decode("utf-8"), bpm_pattern)
    except ValueError:
        print("ERROR BPM")
        print(path)


def extract_length(path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        return extract_pattern(result.stdout.decode("utf-8"), time_pattern)
    except ValueError:
        print("ERROR Length")
        print(path)


def date2year(date: str) -> int:
    """Transform date string to year int."""
    if len(date) == 4:
        return int(date)

    return int(date[:4])


def format_genres(genres: str) -> str:
    """Replaces `/` and spaces by `;`"""
    return genres.replace("/", ";").replace(" & ", ";").replace(" ", ";")


def format_artists(artists: str) -> str:
    if not artists.find(";"):
        return artists

    a = (
        artists.replace(" feat. ", ";")
        .replace(" featuring ", ";")
        .replace(" feat ", ";")
        .replace(" & ", ";")
    )

    a = a.split(";")
    out = [a[0]]

    for e in a[1:]:
        e = e.split(" (from")[0]
        e = e.split(" from")[0]
        out.append(e)

    return ";".join(out)


LABELS = [
    ("title", str),
    ("albumartist", str),
    ("artist", format_artists),
    ("composer", str),
    ("genre", format_genres),
    ("artistsort", str),
    ("album", str),
    ("bpm", lambda x: int(round(float(x)))),
]


def meta(path: str) -> MetaDict:
    """Extract meta of a file of path `path` to a dict."""
    meta = {"path": path}
    m = None

    if path.endswith(".flac"):
        m = FLAC(path)

        for name, func in LABELS + [("originalyear", date2year)]:
            if name in m and m[name] is not None and m[name] != []:
                try:
                    meta[name] = func(m[name][0])
                except KeyError:
                    meta[name] = None
                except IndexError:
                    meta[name] = None
            else:
                meta[name] = None

        meta["year"] = meta["originalyear"]
        del meta["originalyear"]

    elif path.endswith(".mp3"):
        m = EasyID3(path)

        for name, func in LABELS + [("originaldate", date2year), ('date', date2year)]:
            if name in m and m[name] is not None and m[name] != []:
                try:
                    meta[name] = func(m[name][0])
                except KeyError:
                    meta[name] = None
                except IndexError:
                    meta[name] = None
            else:
                meta[name] = None

        if meta['originaldate'] is not None:
            meta["year"] = meta["originaldate"]
        else:
            meta["year"] = meta["date"]

        del meta["originaldate"]
        del meta["date"]
    else:
        return meta

    if meta["bpm"] is None:
        meta["bpm"] = extract_bpm(path)

    meta["length"] = extract_length(path)

    return meta


def walk_path(
    path: str, file_extentions: list[str] = [".mp3", ".flac"]
) -> Iterator[str]:
    for (dirpath, _, filenames) in os.walk(path):
        for filename in filenames:
            for ext in file_extentions:
                if filename.endswith(ext):
                    yield os.path.join(dirpath, filename)
                    break


def count_files(path: str, file_extentions: list[str] = [".mp3", ".flac"]):
    return sum(1 for _ in walk_path(path, file_extentions))


def meta_iter(path: str, check_exists=True, progress_bar=True) -> Iterator[MetaDict]:

    if progress_bar:
        file_count = count_files(path)
        bar = ProgressBar(file_count, "Scanning", use_eta=True)

        try:
            for p in walk_path(path):
                txt = f" {pathlib.Path(p).name[:25]}"
                if not check_exists or check_exists and not DB.path_exists(p):
                    yield meta(p)
                bar.iter(txt)
        except KeyboardInterrupt:
            bar.stop()
        bar.wait()

    else:
        for p in walk_path(path):
            if not check_exists or check_exists and not DB.path_exists(p):
                yield meta(p)


def scan_path(path: str, *args, **kargs) -> None:
    count = 0
    entries = []

    for m in meta_iter(path, *args, **kargs):
        entries.append(m)
        count += 1
        if count % 10 == 0:
            DB.add_entries(entries)
            entries = []

        if count >= 50:
            DB.commit_import()
            count = 0

    DB.add_entries(entries)
    DB.commit_import()


def verify_integrity(progress_bar=True) -> None:
    # TODO: test
    """Deletes entries if their path is no longer valid"""
    if progress_bar:
        file_count = DB.count_entries()
        bar = ProgressBar(file_count, "Scanning", use_eta=True)

        try:
            for p in DB.paths():
                txt = f" {pathlib.Path(p).name[:25]}"
                if not pathlib.Path(p).exists:
                    DB.delete_entry(p)
                bar.iter(txt)
        except KeyboardInterrupt:
            bar.stop()
        bar.wait()

    else:
        for p in DB.paths():
            if not pathlib.Path(p).exists:
                DB.delete_entry(p)
