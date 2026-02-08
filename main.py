#!/usr/bin/env python
from to_ascii import main as to_ascii
from to_kitty import print_kitty
import requests
import random
import shutil
import os, tomllib, PIL
from io import BytesIO
from pathlib import Path
from platformdirs import user_config_dir
import argparse
import base64
import urllib.parse
from dataclasses import dataclass


def b64(s: str) -> str:
    return base64.b64encode(s.encode("ascii")).decode("ascii")

# https://github.com/ClaustAI/r34-api/blob/main/app.py
def ellips(s, mx):
    if len(s) > mx:
        return s[:mx-3]+'...'
    return s

@dataclass
class ReturnObject:
    lowres_url: str
    highres_url: str
    page_url: str
    author: str
    tags: str
    score: str
LIMIT = 100
def get_rule34(auth, tags):
    url = f'https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&limit={LIMIT}&pid=1&tags={tags}&json=1&'+auth
    r = requests.get(url).json()
    req = random.choice(r)
    ret = ReturnObject(
        lowres_url=req['preview_url'],
        highres_url=req['file_url'],
        page_url=f"https://rule34.xxx/index.php?page=post&s=view&id={req['id']}",
        author=req['owner'],
        tags=req['tags'],
        score=req['score']

    )
    return ret


def get_e621(auth, tags):
    params = {"tags": tags, "limit": str(LIMIT)}
    base_url = "https://e621.net/posts.json?"
    url_params = urllib.parse.urlencode(params)
    url = base_url + url_params + "&" + auth
    r = requests.get(url, headers={"User-Agent": "goonfetch/0.1.0 (glacier54)"}).json()["posts"]
    req = random.choice(r)
    ret = ReturnObject(
        lowres_url=req["preview"]["url"],
        highres_url=req["file"]["url"],
        page_url=f"https://e621.net/posts/{req["id"]}",
        author=' '.join(req["tags"]["artist"]),
        tags=" ".join(req["tags"]["general"] + req["tags"]["character"] + req["tags"]["species"]),
        score=req["score"]["total"]
    )
    return ret
def render(ro, ma, protocol):
    if protocol:
        img_bytes = requests.get(ro.highres_url).content
        print_kitty(BytesIO(img_bytes), (int(ma[0]+3), int(ma[1]-4)))
        w,h = ma
    else:
        img_bytes = requests.get(ro.highres_url).content
        w, h = to_ascii(img_bytes, (int(ma[0]), int(ma[1]-4)))
    return w,h

def confparse():
    size = shutil.get_terminal_size(fallback=(60, 24))
    path = Path(user_config_dir("goonfetch")) / "config.toml"
    cfg = tomllib.loads(path.read_text())
    parser = argparse.ArgumentParser(description="Example with optional args")
    parser.add_argument('--max-columns', '-c', type=int, default=size.columns//2, help='Max character columns. Defaults to 1/2 terminal width.')
    parser.add_argument('--max-rows', '-r', type=int, default=size.lines-4, help='Max character rows. Defaults to terminal height.')
    parser.add_argument('--kitty', action='store_true', required=False, help='Use Kitty Graphics Protocol.')
    parser.add_argument('--mode', choices=["rule34", "e621"], default=cfg.get("default", "rule34"), help='Set API call to rule34 or e621.')
    parser.add_argument('additional_tags', nargs='*', help="Add rule34 tags.")
    args = parser.parse_args()
    if not path.exists:
        print("No configuration file detected.")
        exit
    source = args.mode
    conf = cfg.get(source)
    return conf, args

def main(data, ma, protocol):
    w,h = render(data, ma, protocol)
    print(data.page_url)
    print(data.author)
    print(ellips(data.tags, w+3))
    print(f"score: {data.score}")
if __name__ == '__main__':
    conf, args = confparse()
    if not conf:
        raise ValueError("No auth found. You can create an api-key and find your user id/username in the e621.net/rule34.xxx user settings page.")
    match args.mode:
        case 'rule34':
            data = get_rule34(conf['auth'], conf['tags'])
        case 'e621':
            data = get_e621(conf['auth'], conf['tags'])

    main(data, (args.max_columns, args.max_rows+4), args.kitty)
