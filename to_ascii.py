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
def main(imbytes, rc, use_bg=False):
    maw, mah = rc
    maw -= 3
    mah /= 0.55
    mah += 1
    imag = Image.open(imbytes)
    imag.thumbnail((maw, mah), Image.BILINEAR)
    imag = imag.resize((imag.width, int(imag.height * 0.55)), Image.BILINEAR)
    img = np.array(imag.convert('RGB'))
    dist = np.linalg.norm(img, axis=2)

    n = len(chars)
    idx = np.clip((dist/np.percentile(dist, 98)*(n-1)).astype('uint8'), 0, n-1)
    for i in range(img.shape[0]):
        s = ''
        for j in range(img.shape[1]):
            if use_bg:
                bg = fg = img[i, j]
                x = ' '
                isBold = False
            else:
                fg = img[i, j]
                bg = None
                x_o = idx[i, j]
                x = chars[x_o]
                isBold = False
            s += ansi(x, fg, bg, isBold=isBold)
        print(f'{i:02d} '+s)
    return img.shape[:-1][::-1]
if __name__ == '__main__':
    with open('image.png', 'rb') as f:
        by = f.read()
    main(by, (60, 60*0.55))
