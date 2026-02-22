#!/usr/bin/env python
from to_ascii import main as to_ascii
from to_kitty import print_kitty as to_kitty
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
import subprocess
import time
import threading
import sys
import os
import selectors


#UNIX key polling
try:
    import select, termios, tty
except ImportError:
    select = termios = tty = None


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

def raise_reqfail(resp, **text):
    if not 'info' in text:
        text['info']="API call returned unexpected response"
    text['statuscode'] = resp.status_code
    text['response'] = resp.text[:300]
    text['url_used'] = resp.url        # super useful
    print(text)
    raise RuntimeError(text['info']+" (see console output above error)")

def get(url, params):
    resp = requests.get(url, params=params, headers={"User-Agent": "goonfetch/0.1.x"})
    if resp.status_code != 200:
        raise_reqfail(resp)
    if resp.text == '':
        raise_reqfail(resp, info="No posts found from criteria.")
    try:
        dat = resp.json()
    except requests.exceptions.JSONDecodeError:
        raise_reqfail(resp, info="Response was not in JSON format.")
    if not dat:
        raise_reqfail(resp, info="No posts found from criteria.")
    return dat

def get_booru(base, parms):
    parms['page'] = 'dapi'
    parms['s'] = 'post'
    parms['q'] = 'index'
    parms['limit'] = LIMIT
    parms['pid'] = 0 #changed from 1 to 0 to show tags with few pieces of media
    parms['json'] = 1
    url = base
    data = get(url, parms)
    posts = data["post"] if isinstance(data, dict) and "post" in data else data
    if not posts:
        raise RuntimeError("No posts returned (check tags/auth).")
    if not isinstance(posts, list):
        print(posts)
        raise RuntimeError(f"Unexpected format (check tags/auth): {posts}")
    req = random.choice(posts)
    ret = ReturnObject(
        lowres_url=req['preview_url'],
        highres_url=req['file_url'],
        page_url=f"https://{urllib.parse.urlparse(base).netloc}/index.php?page=post&s=view&id={req['id']}",
        author=req['owner'],
        tags=req['tags'],
        score=req['score']

    )
    return ret

def get_e621(parms):
    parms['limit'] = LIMIT
    base_url = "https://e621.net/posts.json/"
    resp = get(base_url, parms)['posts']
    if not resp:
        raise RuntimeError("No posts found.")
    req = random.choice(resp)
    ret = ReturnObject(
        lowres_url=req["preview"]["url"],
        highres_url=req["file"]["url"],
        page_url=f"https://e621.net/posts/{req["id"]}",
        author=' '.join(req["tags"]["artist"]),
        tags=" ".join(req["tags"]["general"] + req["tags"]["character"] + req["tags"]["species"]),
        score=req["score"]["total"]
    )
    return ret



def video_frames(url, fps=8, seconds=3, stop_check=None):    # Uses ffmpeg to stream video frames as PNGs and yield them for real-time ASCII rendering.
    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-headers", "Referer: https://gelbooru.com/\r\n",    # Headers are used so you don't get blocked from the site as queries are made repeatedly during video playback..
        "-user_agent", "Mozilla/5.0",
        "-i", url,
        "-vf", f"fps={fps}",
        "-f", "image2pipe",
        "-vcodec", "png",
        "pipe:1",
    ]

    if seconds is not None:
        cmd.insert(cmd.index("-f"), "-t")
        cmd.insert(cmd.index("-f"), str(seconds))

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,   # stops stderr spam + avoids clogging
        bufsize=0
    )

    png_end = b"IEND\xaeB`\x82"
    buf = b""

    sel = selectors.DefaultSelector()
    try:
        # Make stdout non-blocking (Linux)
        os.set_blocking(p.stdout.fileno(), False)
        sel.register(p.stdout, selectors.EVENT_READ)

        while True:
            # Fast stop check (runs constantly even if ffmpeg stalls)
            if stop_check and stop_check():
                return

            # If ffmpeg already exited, drain what’s left then finish
            if p.poll() is not None:
                while True:
                    try:
                        chunk = os.read(p.stdout.fileno(), 65536)
                    except BlockingIOError:
                        break
                    if not chunk:
                        break
                    buf += chunk

                # Parse any remaining complete PNG frames
                while True:
                    idx = buf.find(png_end)
                    if idx == -1:
                        break
                    frame = buf[:idx + len(png_end)]
                    buf = buf[idx + len(png_end):]
                    yield frame

                    if stop_check and stop_check():
                        return

                return  # ffmpeg is done, nothing more coming

            # Wait briefly for output so stop remains responsive
            events = sel.select(timeout=0.05)
            if not events:
                continue

            try:
                chunk = os.read(p.stdout.fileno(), 65536)
            except BlockingIOError:
                continue

            if not chunk:
                continue

            buf += chunk

            # Extract frames from buffer
            while True:
                idx = buf.find(png_end)
                if idx == -1:
                    break
                frame = buf[:idx + len(png_end)]
                buf = buf[idx + len(png_end):]
                yield frame

                # Check right after yielding so Enter feels instant
                if stop_check and stop_check():
                    return

    finally:
        try:
            sel.unregister(p.stdout)
        except Exception:
            pass
        try:
            sel.close()
        except Exception:
            pass
        try:
            p.terminate()
        except Exception:
            pass
        try:
            p.stdout.close()
        except Exception:
            pass
        try:
            p.wait(timeout=0.2)
        except Exception:
            pass



class RawMode:                                                      # Helpers are used so pressing 'enter' stops the video quickly.
    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)      # Enter becomes immediate
        return self

    def __exit__(self, exc_type, exc, tb):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)

def enter_pressed_nonblocking():
    r, _, _ = select.select([sys.stdin], [], [], 0)
    if not r:
        return False
    ch = sys.stdin.read(1)
    return ch in ("\n", "\r")




def render(ro, ma, protocol):
    url = ro.highres_url
    ext = url.split("?")[0].lower().rsplit(".", 1)[-1]
    
    if ext in ("webm", "mp4", "gif") and not protocol:
        fps = 8
        frame_delay = 1.0 / fps

        print("Press Enter to stop animation...")
        print("\033[2J\033[H\033[0G", end="")

        with RawMode():
            while True:                                                  #Loops video until enter pressed.
                for frame in video_frames(url, fps=fps, seconds=None):
                    print("\033[2J\033[H\033[0G", end="")
                    to_ascii(BytesIO(frame), (int(ma[0]), int(ma[1]-4)))

                    if enter_pressed_nonblocking():
                        return ma

                    time.sleep(frame_delay)

        return ma

    #normal images
    headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://gelbooru.com/",
    }

    resp = requests.get(url, headers=headers, timeout=20)
    ctype = resp.headers.get("Content-Type", "").lower()

    if resp.status_code != 200 or "text/html" in ctype:
       #fallback to preview image if generation fails
        resp = requests.get(ro.lowres_url, headers=headers, timeout=30)


    img_bytes = resp.content

    if protocol:
            print_kitty(BytesIO(img_bytes), (int(ma[0]+3), int(ma[1]-4)))
            w, h = ma
    else:
        w, h = to_ascii(BytesIO(img_bytes), (int(ma[0]), int(ma[1]-4)))

    return w, h




def confparse():
    size = shutil.get_terminal_size(fallback=(60, 24))
    path = Path(user_config_dir("goonfetch")) / "config.toml"
    cfg = tomllib.loads(path.read_text())
    parser = argparse.ArgumentParser(description=f"A rule34 fetching tool. Requires a config.toml to exist. For more information go to https://github.com/glacier54/goonfetch")
    parser.add_argument('--max-columns', '-c', type=int, default=size.columns, help='Max character columns. Defaults to terminal width.')
    parser.add_argument('--max-rows', '-r', type=int, default=size.lines-7, help='Max character rows. Defaults to terminal height.')
    parser.add_argument('--no-ascii', action='store_true', required=False, help='Use either kitty image protocol (when available) or a pixelated image instead of ascii.')
    parser.add_argument('--mode', choices=["rule34", "e621", "gelbooru"], default=cfg.get("default", "rule34"), help='Set API provider.')
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
        raise ValueError("No auth found. You can create an api-key and find your user id/username in the mode's user settings page.")
    if conf.get('auth'):
        conf.update(urllib.parse.parse_qs(conf['auth']))
        conf.pop("auth", None)
    tags = conf.get("tags", "")
    if args.additional_tags:
        conf['tags'] = (tags + " " + " ".join(args.additional_tags)).strip()
    match args.mode:
        case 'rule34':
            data = get_booru('https://rule34.xxx/index.php', conf)
        case 'e621':
            data = get_e621(conf)
        case 'gelbooru':
            data = get_booru('https://gelbooru.com/index.php', conf)

    main(data, (args.max_columns, args.max_rows+4), args.no_ascii)
