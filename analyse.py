import argparse
import os
import re
import subprocess
from typing import Any, Iterator, Union

from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC

from flacduration import get_flac_duration

bpm_pattern = re.compile(r"(\d+|\d+.\d+) BPM$")


def exec_bpm_tag(path: str) -> str:
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
    return stdout.decode("utf-8")


def extract_bpm(output: str) -> int:
    match = bpm_pattern.search(output)
    if match:
        return round(float(match.group(1)))
    return 0


def date2year(date: str) -> int:
    if len(date) == 4:
        return int(date)

    return int(date[:4])


LABELS = [
    ("title", str),
    ("albumartist", str),
    ("artist", str),
    ("composer", str),
    ("genre", str),
    ("artistsort", str),
    ("album", str),
    ("bpm", lambda x: int(round(float(x)))),
    ("length", int),
]


def meta(path: str) -> dict[str, Union[str, int]]:
    meta = {}
    m: dict[str, Any] = None

    if path.endswith(".flac"):
        m = FLAC(path)
        meta["year"] = int(m["originalyear"][0])

        for name, func in LABELS:
            if name in m and m[name] is not None:
                meta[name] = func(m[name][0])

        if "length" not in meta:
            meta["length"] = round(get_flac_duration(path))

    elif path.endswith(".mp3"):
        m = EasyID3(path)
        meta["year"] = date2year(m["date"][0])

        for name, func in LABELS:
            if name in m and m[name] != []:
                meta[name] = func(m[name][0])
    else:
        return {}

    if "bpm" not in meta:
        meta["bpm"] = extract_bpm(exec_bpm_tag(path))

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


def meta_iter(path: str) -> Iterator[dict[str, Any]]:
    for p in walk_path(path):
        yield meta(p)


def main():

    parser = argparse.ArgumentParser(prog="analyzer")
    parser.add_argument("-p", "--path", help="path to scan", nargs=1)
    args = vars(parser.parse_args())

    path = args["path"][0]
    print(path)

    for m in meta_iter(path):
        for k in m:
            print(f"{k}: {m[k]}")

        print("---")


main()
