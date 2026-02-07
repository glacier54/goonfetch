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



# https://github.com/ClaustAI/r34-api/blob/main/app.py
def ellips(s, mx):
    if len(s) > mx:
        return s[:mx-3]+'...'
    return s

def get_images(auth, tags):
    url = f'https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&limit=100&pid=1&tags={tags}&json=1&'+auth
    r = requests.get(url).json()
    return random.choice(r)
def main(obj, ma, protocol):
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
if __name__ == '__main__':
    size = shutil.get_terminal_size(fallback=(60, 24))
    parser = argparse.ArgumentParser(description="Example with optional args")
    parser.add_argument('--max-columns', '-c', type=int, default=size.columns//2, help='Max character columns. Defaults to 1/2 terminal width.')
    parser.add_argument('--max-rows', '-r', type=int, default=size.lines-4, help='Max character rows. Defaults to terminal height.')
    parser.add_argument('--kitty', action='store_true', required=False, help='Use Kitty Graphics Protocol.')
    parser.add_argument('additional_tags', nargs='*', help="Add rule34 tags.")
    args = parser.parse_args()
    path = Path(user_config_dir("goonfetch")) / "config.toml"
    if not path.exists:
        print("No configuration file detected.")
        exit
    cfg = tomllib.loads(path.read_text())
    if not cfg.get('auth'):
        print("No auth found. You can create an api-key and find your user id in the rule34.xxx account settings page.")
    auth = cfg.get('auth')
    main(get_images(auth, cfg.get('tags')+' '+' '.join(args.additional_tags)), (args.max_columns, args.max_rows+4), args.kitty)
