#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import argparse
import pathlib
import argcomplete
from database import DB
from query import QueryColumn
import analyse
import playlist


def main(**args):
    if args["option_list"] is not None:
        cols = {
            "artists": QueryColumn(name="artist", table="library"),
            "albumartists": QueryColumn(name="albumartist", table="library"),
            "years": None,
            "bpm": QueryColumn(name="bpm", table="library"),
            "genres": QueryColumn(name="name", table="genres"),
        }

        for e in DB.column(cols[args["option_list"][0]]):
            print(e)

    if args["sync"] is not None:
        analyse.scan_path(args["sync"][0])

    if args["playlist"]:
        creator = playlist.Creator()

        if args["bpm_min"] is not None or args["bpm_max"] is not None:
            if args["bpm_min"] is not None:
                creator = creator.with_bpm_lower_bound(args["bpm_min"][0])
            if args["bpm_max"] is not None:
                creator = creator.with_bpm_upper_bound(args["bpm_max"][0])
        else:
            if args["bpm_range"] is not None:
                creator = creator.with_bpm_bounds(
                    args["bpm_range"][0], args["bpm_range"][1]
                )
            if args["bpm_window"] is not None:
                creator = creator.with_bpm_bounds(
                    args["bpm_window"][0] - args["bpm_window"][1],
                    args["bpm_window"][0] + args["bpm_window"][1],
                )
        if args["length_min"] is not None:
            creator = creator.with_length_lower_bound(args["length_min"][0])
        if args["length_max"] is not None:
            creator = creator.with_length_upper_bound(args["length_max"][0])

        if args["random"]:
            creator = creator.with_random()

        if args["artist_restrict"] is not None:
            creator = creator.with_artist_restrict(args["artist_restrict"])
        if args["artist_exclude"] is not None:
            creator = creator.with_artist_exclude(args["artist_exclude"])

        if args["genre_restrict"] is not None:
            creator = creator.with_genres_restrict(args["genre_restrict"])
        if args["genre_exclude"] is not None:
            creator = creator.with_genres_exclude(args["genre_exclude"])

        if args["time_length"] is not None:
            creator = creator.with_length(args["time_length"][0])

        if args["root"] is not None:
            creator = creator.with_root(args["root"][0])

        p = creator.generate_playlist()

        if not args["quiet"]:
            print(p)

        if args["out"] is not None:
            with open(args["out"][0], "w") as f:
                f.write(p.to_m3u())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="analyzer")
    parser.add_argument(
        "-q",
        "--quiet",
        help="Disable prints to stdout in playlist creation mode",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--sync",
        help="Sync and analyse files in path",
        nargs=1,
        metavar="PATH",
        type=pathlib.Path,
    )
    parser.add_argument(
        "-p",
        "--playlist",
        help="Create a playlist",
        action="store_true",
    )
    parser.add_argument(
        "-o", "--out", help="Destination file for playlist", type=pathlib.Path, nargs=1
    )
    parser.add_argument(
        "-r",
        "--root",
        help="Root path of the music library. Removes the root from every track path",
        type=pathlib.Path,
        nargs=1,
    )
    parser.add_argument("-b", "--bpm-min", help="BPM min wanted", nargs=1, type=int)
    parser.add_argument("-B", "--bpm-max", help="BPB max wanted", nargs=1, type=int)
    parser.add_argument(
        "-R", "--bpm-range", help="BPM range", nargs=2, metavar=("BPM_MIN", " BPM_MAX")
    )
    parser.add_argument(
        "-w",
        "--bpm-window",
        help="BPM wanted with margin of error",
        nargs=2,
        type=int,
        metavar=("BPM", "MARGIN"),
    )
    parser.add_argument(
        "-a",
        "--artist-restrict",
        help="Restrict to artists",
        action="extend",
        nargs="+",
        type=str,
        metavar="ARTIST",
        choices=DB.column(QueryColumn(name="artist", table="library"))
        + DB.column(QueryColumn(name="albumartist", table="library")),
    )
    parser.add_argument(
        "-A",
        "--artist-exclude",
        help="Exclude artists",
        action="extend",
        nargs="+",
        type=str,
        metavar="ARTIST",
        choices=DB.column(QueryColumn(name="artist", table="library"))
        + DB.column(QueryColumn(name="albumartist", table="library")),
    )
    parser.add_argument(
        "-g",
        "--genre-restrict",
        help="Restrict to genres",
        action="extend",
        nargs="+",
        type=str,
        metavar="GENRE",
        choices=DB.column(QueryColumn(name="name", table="genres")),
    )
    parser.add_argument(
        "-G",
        "--genre-exclude",
        help="Exclude genres",
        action="extend",
        nargs="+",
        type=str,
        metavar="GENRE",
        choices=DB.column(QueryColumn(name="name", table="genres")),
    )
    parser.add_argument(
        "-l", "--length-min", help="Track length min wanted", nargs=1, type=int
    )
    parser.add_argument(
        "-L", "--length-max", help="Track length max wanted", nargs=1, type=int
    )
    parser.add_argument(
        "-t",
        "--time-length",
        help="Wanted time length of the playlist",
        nargs=1,
        type=int,
    )
    parser.add_argument(
        "-y",
        "--year-restrict",
        help="Restrict to years",
        action="extend",
        nargs="+",
        type=int,
        metavar="YEAR",
    )
    parser.add_argument(
        "-O",
        "--option-list",
        help="List availabe: artists|albumartists|years|bpm",
        nargs=1,
        type=str,
        choices=["artists", "albumartists", "years", "bpm", "genres"],
        metavar="OPTION",
    )
    parser.add_argument(
        "-u", "--random", action="store_true", help="Randomize playlist"
    )

    parser.add_argument(
        "-m",
        "--mutate-mp3",
        action="store_true",
        help="All files are considered MP3 files (output only)",
    )

    argcomplete.autocomplete(parser)
    args = vars(parser.parse_args())
    main(**args)
