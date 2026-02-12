from io import BytesIO
from typing import Tuple
from PIL import Image as pillow_image
from rich.console import Console
from textual_image.renderable.tgp import Image

def print_kitty(imbytes: BytesIO, rc) -> None:
    console = Console()
    maw, mah = rc
    maw -= 3
    mah += 1
    imag = pillow_image.open(imbytes)
    w_o, h_o = imag.size
    if h_o*0.55/mah > w_o/maw:
        w, h = int(w_o*mah/h_o/0.55), mah
    else:
        w, h = maw, int(h_o*maw/w_o*0.55)
    console.print(Image(imag, width=w+3, height=h))
    return w, h
