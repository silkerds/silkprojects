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
    "User-Agent": "silkpuller v1.0.0 https://github.com/silkerds/silkprojects"
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

#-------------------------------------

def getpath():
    print("will search recursively inside the directory you choose for files and other folders")
    print("what path to look for music in?")
    while options["pathready"] == False:
        options["path"] = Path(f"/{input("/")}")
        if options["path"].exists():
            options["pathready"] = True

def getoptions():
    while options["go"] == False:
        nonamevars[1] = False
        while nonamevars[1] == False:
            nonamevars[1] = True
            pppp = input("replace pre-existing lyrics? (y/N) ")
            
            if pppp in yes:
                options["replace"] = True
                print("will replace duplicate files")
                nonamevars
            elif pppp in no:
                options["replace"] = False
                print("will not replace duplicate files")
            elif pppp == "":
                options["replace"] = False
                print("defaulting to no replacing")
            else:
                nonamevars[1] = False
            

        nonamevars[1] = False
        while nonamevars[1] == False:
            nonamevars[1] = True
            qqqq = input("if synced lyrics not found, save plain lyrics? (y/N) ")
            
            if qqqq in yes:
                options["plain"] = True
                print("will save plain lyrics")
            elif qqqq in no:
                options["plain"] = False
                print("will not save plain lyrics")
            elif qqqq == "":
                options["plain"] = False
                print("defaulting to no plain lyrics")
            else:
                nonamevars[1] = False
        
        nonamevars[1] = False
        while nonamevars[1] == False:
            nonamevars[1] = True
            conf = (input("confirm? (y/N) "))

            if conf in yes:
                options["go"] = True
            elif conf in no or conf == "":
                print("restarting")
            else:
                nonamevars[1] = False

    print("press c or q then enter to cancel")
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

#-------------------------------------

def lrcget(path):
    global roger
    for file in path.rglob("*"):
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
            else:
                stats["errors"]["metadata"] += 1
                roger = "metadata error"
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

def result(file):
    print(f"{file.name} -- {roger}")

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
        time.sleep(int(status.headers["Retry-After"]))
        request(file)
    elif status.status_code == 503:
        stats["errors"][503] += 1
        time.sleep(.3)
        request(file)
    elif status.status_code == 404:
        roger = ("no lyrics found")
        stats["lyrics"]["missing"] += 1
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
    else:
        stats["errors"]["unknownstatus"] += 1
        roger = "unknown status code"


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
    else:
        stats["errors"]["badlrclib"] += 1
        roger = "lrclib error"

def ready():
    for field in nonamevars:
        nonamevars[field] = False

#-------------------------------------

def endstats():
    global errors
    print("------------End Statistics.------------")
    if stats["files"]["songs"] != 0:
        print(f"songs checked -- {stats["files"]["songs"]}")
    if stats["lyrics"]["found"] != 0:
        print(f"    found new lyrics -- {stats["lyrics"]["found"]}")
    if stats["lyrics"]["replaced"] != 0:
        print(f"    replaced lyrics -- {stats["lyrics"]["replaced"]}")
    if stats["lyrics"]["plain"] != 0:
        print(f"    saved plain lyrics -- {stats["lyrics"]["plain"]}")
    if stats["lyrics"]["skipped"] != 0:
        print(f"    skipped lyrics -- {stats["lyrics"]["skipped"]}")
    if stats["lyrics"]["missing"] != 0:
        print(f"    missing lyrics -- {stats["lyrics"]["missing"]}")
    print("---------------------------------------")
    for value in stats["errors"]:
        errors += stats["errors"][value]

def errorprint():    
    print(f"you have {errors} errors,")
    time.sleep(.7)
    while nonamevars[2] == False:
        nonamevars[2] = True
        secret = input("would you like to view them? (y/N) ")
        if secret in yes:
            for key, value in stats["errors"].items():
                print(f"{key}: {value}")
        elif secret in no or secret == "":
            break
        else:
            nonamevars[2] = False

#-------------------------------------

def main():
    welcome()
    pause()
    disclaimer()
    pause()
    getpath()
    pause()
    getoptions()
    pause()

    lrcget(options["path"])
    pause()

    endstats()
    pause()
    if errors != 0:
        errorprint()
    pause()
    print("----Thank you for using silkpuller!----")

#-------------------------------------

def pause():
    print(" ")
    time.sleep(.5)

if __name__ == "__main__":
    main()
