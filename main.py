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


def b64(s: str) -> str:
    return base64.b64encode(s.encode("ascii")).decode("ascii")

# https://github.com/ClaustAI/r34-api/blob/main/app.py
def ellips(s, mx):
    if len(s) > mx:
        return s[:mx-3]+'...'
    return s

def get_images(auth, tags, source):
    LIMIT = 100
    match source:
        case "rule34":
            url = f'https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&limit={LIMIT}&pid=1&tags={tags}&json=1&'+auth
            r = requests.get(url).json()
        case "e621":
            params = {"tags": tags, "limit": str(LIMIT)}
            base_url = "https://e621.net/posts.json?"
            url_params = urllib.parse.urlencode(params)

            url = base_url + url_params
            r = requests.get(url, headers=auth).json()["posts"]

    return random.choice(r)
def main(obj, ma, protocol, source):
    match source:
        case "rule34":
            if protocol:
                img_bytes = requests.get(obj['file_url']).content
                print_kitty(BytesIO(img_bytes), (int(ma[0]), int(ma[1]-4)))
                w = ma[0]
            else:
                img_bytes = requests.get(obj['preview_url']).content
                w, _ = to_ascii(img_bytes, (int(ma[0]), int(ma[1]-4)))
            print(f"https://rule34.xxx/index.php?page=post&s=view&id={obj['id']}")
            print(obj['owner'])
            print(ellips(obj['tags'], w+3))
            print(f"score: {obj['score']}")
        case "e621":
            if protocol:
                img_bytes = requests.get(obj["file"]["url"]).content
                print_kitty(BytesIO(img_bytes), (int(ma[0]), int(ma[1]-4)))
                w = ma[0]
            else:
                img_bytes = requests.get(obj["preview"]["url"]).content
                w, _ = to_ascii(img_bytes, (int(ma[0]), int(ma[1]-4)))
            print(f"https://e621.net/posts/{obj["id"]}")
            print(*obj["tags"]["artist"])
            print(ellips(" ".join(obj["tags"]["general"] + obj["tags"]["character"] + obj["tags"]["species"]), w+3))
            print(f"score: {obj["score"]["total"]}")
if __name__ == '__main__':
    size = shutil.get_terminal_size(fallback=(60, 24))
    parser = argparse.ArgumentParser(description="Example with optional args")
    parser.add_argument('--max-columns', '-c', type=int, default=size.columns//2, help='Max character columns. Defaults to 1/2 terminal width.')
    parser.add_argument('--max-rows', '-r', type=int, default=size.lines-4, help='Max character rows. Defaults to terminal height.')
    parser.add_argument('--kitty', action='store_true', required=False, help='Use Kitty Graphics Protocol.')
    parser.add_argument('--e621', action='store_true', required=False, help='Fetch from e621 instead.')
    parser.add_argument('additional_tags', nargs='*', help="Add rule34 tags.")
    args = parser.parse_args()
    path = Path(user_config_dir("goonfetch")) / "config.toml"
    if not path.exists:
        print("No configuration file detected.")
        exit
    cfg = tomllib.loads(path.read_text())

    source = "e621" if args.e621 else "rule34"
    match source:
        case "e621":
            e621_username = cfg.get("e621_username")
            e621_api_key = cfg.get("e621_api_key")
            tags = cfg.get('tags')
            if e621_username is None or e621_api_key is None:
                raise ValueError("No auth found. You can create an api-key and find your user id in the e621.net user settings page.")
            e621_user_agent = f"goonfetch/0.1.0 ({e621_username})"
            auth = {
            "Authorization": "Basic " + b64(f"{e621_username}:{e621_api_key}"),
            "User-Agent": e621_user_agent,
                }

        case "rule34":
            if not cfg.get('auth'):
                print("No auth found. You can create an api-key and find your user id in the rule34.xxx account settings page.")
            auth = cfg.get('auth')
            tags = cfg.get('tags')
        case _:
            raise AssertionError("Invalid source")

    if tags is None:
        tags = ""

    main(get_images(auth, tags+' '+' '.join(args.additional_tags), source), (args.max_columns, args.max_rows+4), args.kitty, source)
