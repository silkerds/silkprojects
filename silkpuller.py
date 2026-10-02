#silkpuller
#pulls lyrics from lrclib according to song files you have
#a python learning project
import requests
from pathlib import Path
from mutagen import File
import time
import os
import sys
import select
import json

#-------------------------------------

metadata = {
    "title": None,
    "artist": None,
    "album": None,
}

query = {
    "track_name": None,
    "artist_name": None,
    "album_name": None,
    "duration": None
}

lrclib_url = "https://lrclib.net/api/get"

headers = {
    "User-Agent": "silkpuller v1.0.3 https://github.com/silkerds/silkprojects"
}

existvar = {
    "lrcfile": False,
    "txtfile": False,
    "lrcfilef": None,
    "txtfilef": None
}

#-------------------------------------

errors = 0

stats = {
    "files": {
        "songs": 0
    },
    "lyrics": {
        "found": 0,
        "replaced": 0,
        "plain": 0,
        "skipped": 0,
        "missing": 0
    },
    "errors": {
        "badlrclib": 0,
        429: 0,
        503: 0,
        "unknownstatus": 0,
        "metadata": 0
    }
}

options = {
    "go": False,
    "replace": False,
    "plain": False,
    "pathready": False,
    "path": None,
    "whatdidido": None
}

yes = [
    "y",
    "Y",
    "yes",
    "Yes"
]
no = [
    "n",
    "N",
    "No",
    "no"
]

#supported status codes are
#   200
#   404
#   429
#   503

nonamevars = {
    1: False,
    2: False,
    3: False,
    4: False,
    5: False,
    6: False,
    7: False,
    8: False,
    9: False,
    0: False
}

supportedtypes = [
    ".flac",
    ".mp3",
    ".ogg",
    ".m4a",
    ".mp4",
    ".opus",
    ".wav",
    ".aac"
]

roger = None

requiredmetadata = {
    "title": [
        "TIT2",
        "title",
        "TITLE",
        "©nam"
    ],
    "artist": [
        "TPE1",
        "artist",
        "ARTIST",
        "©ART"
    ],
    "album": [
        "TALB",
        "album",
        "ALBUM",
        "©alb"
    ]
}

statfiles = {
    "missingl": "silkpuller-missinglyr.txt",
    "plainl": "silkpuller-plainlyr.txt",
    "badmetal": "silkpuller-badmeta.txt",
}

#-------------------------------------

def welcome():
    print("silkpuller - a python learning project")
    time.sleep(1)
    print("silkpuller gets lyrics for your music")
    print("it...")
    print("     pulls lyrics from lrclib")
    print("     searches for music recursively in a directory")
    print("     and it supports multiple metadata tags for multiple audio filetypes")

def disclaimer():
    print("make sure your music has metadata for its artist, title, and album")
    print("by default replaces .txt lyric files (with the naming convention from this script)")
    print("with .lrc synced lyric files if the .txt exists and it finds synced lyrics")
    print("makes a file in whatever directory you point it at that contains dumps for diagnostics if an error happens")
    print("./silkpuller-errors.txt")

#-------------------------------------

def getpath():
    print("will search recursively inside the directory you choose for files and other folders")
    print("what path to look for music in?")
    while options["pathready"] == False:
        options["path"] = Path(f"/{input("/")}")
        if options["path"].exists():
            nonamevars[3] = input("confirm? (Y/n) ")
            if nonamevars[3] in yes:
                options["pathready"] = True
            elif nonamevars[3] == "":
                options["pathready"] = True

def getoptions():
    while options["go"] == False:
        nonamevars[1] = False
        while nonamevars[1] == False:
            nonamevars[1] = True
            pppp = input("replace pre-existing lyrics? (y/N) ")
            
            if pppp in yes:
                options["replace"] = True        
            elif pppp in no or pppp == "":
                options["replace"] = False
            else:
                nonamevars[1] = False
            

        nonamevars[1] = False
        while nonamevars[1] == False:
            nonamevars[1] = True
            qqqq = input("if synced lyrics not found, save plain lyrics? (y/N) ")
            
            if qqqq in yes:
                options["plain"] = True
            elif qqqq in no or qqqq == "":
                options["plain"] = False
            else:
                nonamevars[1] = False
        
        nonamevars[1] = False
        while nonamevars[1] == False:
            nonamevars[1] = True
            conf = (input("confirm? (Y/n) "))

            if conf in yes or conf == "":
                options["go"] = True
            elif conf in no:
                print("restarting")
            else:
                nonamevars[1] = False

    print("")
    print("press c or q then enter to cancel")
    time.sleep(.5)
    for i in range(1, 4):
        print(i)

        ready, _, _ = select.select([sys.stdin], [], [], 1)

        if ready:
            key = sys.stdin.readline().strip().lower()

            if key in ["c", "q"]:
                options["go"] = False
                getoptions()
                break

    print("continuing")
    time.sleep(.3)

#-------------------------------------

def lrcget(path):
    for value in statfiles:
        f = path / value
        f.unlink(missing_ok=True)

    errorfile = path / "silkpuller-errors.txt"
    with open(errorfile, "w") as f:
        f.write("silkpuller error log\n\n")

    global roger
    for file in path.rglob("*"):
        call = None
        if file.suffix in supportedtypes:
            stats["files"]["songs"] += 1
            for field in existvar:
                existvar[field] = False
            if file.with_suffix(".lrc").exists():
                existvar["lrcfile"] = True
                existvar["lrcfilef"] = file.with_suffix(".lrc")
            if file.with_suffix(".txt").exists():
                existvar["txtfile"] = True
                existvar["txtfilef"] = file.with_suffix(".txt")
            try:
                audio = File(file)
                if metacheck(audio):
                    roger = "roger was not written, find out why"
                    if not existvar["lrcfile"] or options["replace"]:
                        options["whatdidido"] = "new"
                        if( 
                            existvar["lrcfile"] and
                            options["replace"]
                        ):
                            options["whatdidido"] = "exist"
                        request(file) 
                    elif(
                        existvar["lrcfile"] and
                        not options["replace"]
                    ):
                        stats["lyrics"]["skipped"] += 1
                        roger = "lyrics already exist"
                        call = "skipped"
                else:
                    stats["errors"]["metadata"] += 1
                    roger = "metadata error"
                    lyriclog(file, "meta", audio)
            except Exception as error:
                roger = f"unhandled error - {error}"
            if not call is None:
                result(file, call)
            else:
                result(file)
            
def metacheck(audio):
    for field in metadata:
        metadata[field] = None
    for field in query:
        query[field] = None

    for field in requiredmetadata:
        for tag in requiredmetadata[field]: 
            if audio.get(tag):
                metadata[field] = audio[tag][0]
                break

    query["track_name"] = metadata["title"]
    query["artist_name"] = metadata["artist"]
    query["album_name"] = metadata["album"]
    query["duration"] = round(audio.info.length)
    
    return all(metadata[field] is not None for field in requiredmetadata)

def result(file, call=None):
    print(f"{file.name} -- {roger}")
    if call is None:
        time.sleep(.2)

def request(file):
    status = requests.get(
        url=lrclib_url,
        headers=headers,
        params=query
    )

    statushandler(status, file)

def statushandler(status, file):
    global roger
    if status.status_code == 429:
        stats["errors"][429] += 1
        roger = "rate limit, retrying"
        result(file)
        time.sleep(int(status.headers["Retry-After"]))
        request(file)
    elif status.status_code == 503:
        stats["errors"][503] += 1
        roger = "503 error, retrying"
        result(file)
        time.sleep(1)
        request(file)
    elif status.status_code == 404:
        roger = ("no lyrics found")
        stats["lyrics"]["missing"] += 1
        lyriclog(file, "missing")
    elif status.status_code == 200:
        data = status.json()
        if data["instrumental"]:
            roger = "instrumental"
            stats["lyrics"]["skipped"] += 1
        elif not data["instrumental"]:
            writer(data, file)
        else:
            roger = "lrclib error"
            stats["errors"]["badlrclib"] += 1
            errorlog(file, data, "data")
    else:
        stats["errors"]["unknownstatus"] += 1
        roger = "unknown status code"
        errorlog(file, status, "status")

def errorlog(file, dump, dumptype):
    with open(options["path"] / "silkpuller-errors.txt", "a") as f:
        f.write(f"{file.name}\n")

        if dumptype == "status":
            f.write(f"status code: {dump.status_code}\n")
            f.write(f"headers: {dump.headers}\n")
            f.write(f"response: {dump.text}\n")

        elif dumptype == "data":
            f.write("data:\n")
            f.write(json.dumps(dump, indent=4))
            f.write("\n")

        f.write("---------------------------------------\n")

def lyriclog(file, type, audio=None):
    if type == "missing":
        with open(options["path"] / "silkpuller-missinglyr.txt", "a") as f:
            f.write(f"Missing Lyrics\n")
            f.write(f"{file}\n")
    elif type == "plain":
        with open(options["path"] / "silkpuller-plainlyr.txt", "a") as f:
            f.write(f"Plain Lyrics\n")
            f.write(f"{file}\n")
    elif type == "meta":
        with open(options["path"] / "silkpuller-badmetadata.txt", "a") as f:
            f.write(f"Bad Metadata\n")
            f.write(f"{file}\n")
            f.write(f"{audio}")

def writer(data, file):
    global roger
    if data["syncedLyrics"] is not None:
        with open(file.with_suffix(".lrc"), "w") as f:
            f.write(data["syncedLyrics"])
        if existvar["txtfile"]:
            existvar["txtfilef"].unlink(missing_ok=True)
        if options["whatdidido"] == "new":
            stats["lyrics"]["found"] += 1
            roger = "lyrics found"
        elif options["whatdidido"] == "exist":
            stats["lyrics"]["replaced"] += 1
            roger = "replacing current lyrics"
    elif(
        data["plainLyrics"] is not None and
        options["plain"] and
        not existvar["txtfile"] and
        not existvar["lrcfile"]
    ):
        with open(file.with_suffix(".txt"), "w") as f:
            f.write(data["plainLyrics"])
        roger = "saved plain lyrics"
        stats["lyrics"]["plain"] += 1
        lyriclog(file, "plain")
    elif data["plainLyrics"] is not None and not options["plain"]:
        roger = "only plain lyrics found"
        stats["lyrics"]["skipped"] += 1
        return
    else:
        stats["errors"]["badlrclib"] += 1
        roger = "lrclib error"
        errorlog(file, data, "data")

def ready():
    for field in nonamevars:
        nonamevars[field] = False

#-------------------------------------

def endstats():
    global errors
    print("------------End Statistics.------------")
    print("Lyrics -")
    if stats["files"]["songs"] != 0:
        print(f"    songs checked -- {stats["files"]["songs"]}")
    for key, value in stats["lyrics"].items():
        if stats["lyrics"][key] != 0:
            print(f"        {key} lyrics -- {value}")
    print("---------------------------------------")
    for value in stats["errors"]:
        errors += stats["errors"][value]
   
    if errors != 0:
        print("Errors -")
        for key, value in stats["errors"].items():
            if stats["errors"][key] != 0:
                print(f"    {key} -- {value}")

#-------------------------------------

def main():
    welcome()
    disclaimer()
    print("")
    input("read through that if you want, press enter to continue")
    print("")
    getpath()
    pause()
    getoptions()
    pause()

    lrcget(options["path"])
    pause()

    endstats()
    print("----Thank you for using silkpuller!----")

#-------------------------------------

def pause():
    print(" ")
    time.sleep(.5)

if __name__ == "__main__":
    main()
