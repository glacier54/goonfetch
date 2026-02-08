from cv2 import imdecode, resize, IMREAD_COLOR, INTER_LINEAR
import numpy as np

def ansi(x, fg, bg=None, isBold=False):
    parts = []

    # bold on/off (no full reset)
    parts.append("1" if isBold else "22")

    # foreground RGB
    fr, fg_, fb = fg
    parts.append(f"38;2;{fr};{fg_};{fb}")

    # background RGB (optional)
    if bg is not None:
        br, bg_, bb = bg
        parts.append(f"48;2;{br};{bg_};{bb}")

    sgr = ";".join(parts)

    return f"\033[{sgr}m{x}\033[0m"


chars = list(reversed("$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`\'. "))
def main(imbytes, rc):
    maw, mah = rc
    maw -= 3
    arr = np.frombuffer(imbytes, dtype=np.uint8)
    img = imdecode(arr, IMREAD_COLOR)
    h_o, w_o = img.shape[:2]
    if h_o*0.55/mah > w_o/maw:
        w, h = int(w_o*mah/h_o/0.55), mah
    else:
        w, h = maw, int(h_o*maw/w_o*0.55)
    img = resize(img, (w, h), interpolation=INTER_LINEAR)
    wts = np.array([77, 150, 29], dtype=np.uint16)  # uint16 to avoid overflow
    dist = np.sum(img.astype(np.uint16) * wts, axis=2) >> 8  # integer division by 256
    dist = dist.astype(np.uint8)  # optional: back to uint8
    mi, ma = np.percentile(dist, 10), np.percentile(dist, 90)

    n = len(chars)*2
    idx = np.clip(np.uint8((dist-mi)*n/ma), 0, n-1)
    for i in range(h):
        s = ''
        for j in range(w):
            # bb, bg, br = img[i, j]
            fb, fg, fr = img[i, j]
            x_o = idx[i, j]
            # fr, fg, fb = 255, 255, 255
            br, bg, bb = 0, 0, 0
            x = chars[x_o//2]
            isBold = x_o % 2 == 1
            s += ansi(x, (fr, fg, fb), isBold=isBold)
        print(f'{i:02d} '+s)
    return w, h
if __name__ == '__main__':
    with open('image.png', 'rb') as f:
        by = f.read()
    main(by, (60, 60*0.55))
