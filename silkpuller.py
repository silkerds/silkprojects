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
import re
import customtkinter

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
    "User-Agent": "silkpuller v1.0.6 https://github.com/silkerds/silkprojects"
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
    0: False,
    11: False,
    12: False,
    14: False,
    15: False
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
    "inter": {
        "missingl": "silkpuller-missinglyr.txt",
        "plainl": "silkpuller-plainlyr.txt",
        "badmetal": "silkpuller-badmeta.txt",
        "status": "silkpuller-status.txt",
        "api": "silkpuller-api.txt"
    },
    "end": {
        "leftover": "silk-leftover-list.txt",
        "errors": "silkpuller-errors.txt"
    }
}

#-------------------------------------

def welcome():
    print("silkpuller - a python learning project")
    time.sleep(1)
    print("silkpuller gets lyrics for your music")
    print("""it...
        pulls lyrics from lrclib")
        searches for music recursively in a directory")
        and it supports multiple metadata tags for multiple audio filetypes""")

def disclaimer():
    print("""make sure your music has metadata for its artist, title, and album
    by default replaces .txt lyric files (with the naming convention from this script)
    with .lrc synced lyric files if the .txt exists and it finds synced lyrics
    also saves end stat diagnostic files to whatever directory it's run in""")

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

def lrcget():
    path = options["path"]
    for field in nonamevars:
        nonamevars[field] = False

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
                    statlog(file, "meta", audio)
            except Exception as error:
                roger = f"unhandled error - {error}"
            if call is not None:
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

def syntaxchecker(data):
    nonamevars[4] = False
    pattern = r"\[\d+:\d+(?:\.\d+)?\]"
    if re.search(pattern, data["plainLyrics"]):
        pattern = r"\](?=\S)"
        if re.search(pattern, data["plainLyrics"]):
            data["plainLyrics"] = re.sub(
                pattern,
                "] ",
                data["plainLyrics"]
            )
        nonamevars[4] = True
        return(True)
    return(False)

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
        statlog(file, "missing")
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
    elif (
        data["plainLyrics"] is not None and
        syntaxchecker(data)
    ):
        with open(file.with_suffix(".lrc"), "w") as f:
            f.write(data["plainLyrics"])
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
        not existvar["lrcfile"] and
        not nonamevars[4]
    ):
        with open(file.with_suffix(".txt"), "w") as f:
            f.write(data["plainLyrics"])
        roger = "saved plain lyrics"
        stats["lyrics"]["plain"] += 1
        statlog(file, "plain")
    elif(
        data["plainLyrics"] is not None and
        not options["plain"] and
        not nonamevars[4]
    ):
        roger = "only plain lyrics found"
        stats["lyrics"]["skipped"] += 1
        return
    else:
        stats["errors"]["badlrclib"] += 1
        roger = "lrclib error"
        errorlog(file, data, "data")

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

    for i in statfiles["inter"]:
        (options["path"] / statfiles["inter"][i]).unlink(missing_ok=True)

#-------------------------------------

def errorlog(file, dump, dumptype):
    
    if dumptype == "status":
        with open(options["path"] / statfiles["inter"]["status"], "a") as f:
            f.write(f"status code: {dump.status_code}\n")
            f.write(f"headers: {dump.headers}\n")
            f.write(f"response: {dump.text}\n\n")
    elif dumptype == "data":
        with open(options["path"] / statfiles["inter"]["api"], "a") as f:
            f.write("data:\n")
            f.write(json.dumps(dump, indent=4))
            f.write("\n\n")

def errormerge():
    path = options["path"]

    data1 = ""
    data2 = ""

    f = options["path"] / statfiles["inter"]["status"]
    if f.exists():
        data1 = f.read_text()

    f = options["path"] / statfiles["inter"]["api"]
    if f.exists():
        data2 = f.read_text()

    with open(path / statfiles["end"]["errors"], "a") as f:
        f.write(f"""
        ----------- Error List -----------

        Logs for errors relating to what the api returned
        
        Below, there should be entries for
        {stats["errors"]["unknownstatus"]} unknown statuses and
        {stats["errors"]["badlrclib"]} broken return jsons

        ----------- Unknown Status -----------

        {data1}

        ----------- API Side Error -----------
        (or an accidental issue from me)

        {data2}

        ----------- End -----------
        """
        )
    nonamevars[14] = True

def statlog(file, type, audio=None):
    if type == "missing":
        with open(options["path"] / statfiles["inter"]["missingl"], "a") as f:
            f.write(f"{file}\n")
    elif type == "plain":
        with open(options["path"] / statfiles["inter"]["plainl"], "a") as f:
            f.write(f"{file}\n")
    elif type == "meta":
        with open(options["path"] / statfiles["inter"]["badmetal"], "a") as f:
            f.write(f"{file}\n")
            f.write(f"{audio}")

def statmerge():
    path = options["path"]

    data1 = ""
    data2 = ""
    data3 = ""

    f = options["path"] / statfiles["inter"]["missingl"]
    if f.exists():
        data1 = f.read_text()

    f = options["path"] / statfiles["inter"]["plainl"]
    if f.exists():
        data2 = f.read_text()

    f = options["path"] / statfiles["inter"]["badmetal"]
    if f.exists():
        data3 = f.read_text()

    with open(path / statfiles["end"]["leftover"], "w") as f:
        f.write(f"""
        ----------- Leftover Files -----------
        
        Any songs that got skipped for either:
            not finding lyrics
            only finding plain lyrics
            bad metadata
        
        Below, there should be entries for
        {stats["lyrics"]["missing"]} 404s
        {stats["lyrics"]["plain"]} Plain
        {stats["errors"]["metadata"]} bad metadata

        There may also be an error list file if any errors occurred
        if it exists it will be at {path}/{statfiles["end"]["errors"]}

        ----------- 404 Lyrics Not Found -----------
        
        {data1}

        ----------- Only Plain Lyrics Found -----------

        {data2}

        ----------- Bad Metadata -----------

        {data3}

        ----------- End -----------
        """
        )
    nonamevars[15] = True

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

    lrcget()
    pause()

    for field in nonamevars:
        nonamevars[field] = False
    statmerge()
    errormerge()
    endstats()
    print("----Thank you for using silkpuller!----")

#-------------------------------------

def pause():
    print(" ")
    time.sleep(.5)

def cleanup():
    if nonamevars[14] and nonamevars[15]:
        for field in statfiles["inter"]:
            (options["path"] / statfiles["inter"][field]).unlink(missing_ok=True)
    else:
        for k in statfiles:
            for i in statfiles[k]:
                (options["path"] / statfiles[k][i]).unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup()
        print(f"\ncleaning up")
    except Exception as error:
        cleanup()
        print(f"\n error: {error}")
