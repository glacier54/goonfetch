import numpy as np
from PIL import Image
from io import BytesIO


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
    mah /= 0.55
    mah += 1
    imag = Image.open(imbytes).convert('RGB')
    imag.thumbnail((maw, mah), Image.BILINEAR)
    imag = imag.resize((imag.width, int(imag.height * 0.55)), Image.BILINEAR)
    img = np.array(imag, dtype='uint8')
    
    wts = np.array([77, 150, 29], dtype=np.uint16)  # uint16 to avoid overflow
    dist = np.sum(img.astype(np.uint16) * wts, axis=2) >> 8  # integer division by 256
    dist = dist.astype(np.uint8)  # optional: back to uint8
    mi, ma = np.percentile(dist, 10), np.percentile(dist, 90)

    n = len(chars)*2
    idx = np.clip(np.uint8((dist-mi)*n/ma), 0, n-1)
    for i in range(img.shape[0]):
        s = ''
        for j in range(img.shape[1]):
            # bb, bg, br = img[i, j]
            fr, fg, fb = img[i, j]
            x_o = idx[i, j]
            # fr, fg, fb = 255, 255, 255
            br, bg, bb = 0, 0, 0
            x = chars[x_o//2]
            isBold = x_o % 2 == 1
            s += ansi(x, (fr, fg, fb), isBold=isBold)
        print(f'{i:02d} '+s)
    return img.shape[:-1][::-1]
if __name__ == '__main__':
    with open('image.png', 'rb') as f:
        by = f.read()
    main(by, (60, 60*0.55))
