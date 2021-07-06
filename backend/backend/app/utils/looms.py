"""
Copyright 2021 Alee Azam. All rights reserved.
Use of this source code is governed by the MIT
license that can be found in the LICENSE file.
"""

from PIL import Image, ImageDraw
from hashlib import sha1


def _square(image, x, y, block, pad):
    x = x * block + pad
    y = y * block + pad

    image = ImageDraw.Draw(image)
    image.rectangle((x, y, x + block, y + block), fill="#ffffff")


def generate_identicon(seed, width=420, pad=0.15):
    """
    generate creates identicons using the SHA1 hash of the provided seed
    :param seed: (str) the seed used for making the identicon
    :param width: (int, opt) the width of the image in pixels
    :param pad: (int, opt) the margin of the sprite and the image
    :return: PIL.Image object
    ```
    # examples
    generate_identicon("alee").show()
    generate_identicon("looms").save("looms.png")
    ```
    """

    if type(seed) != str:
        raise TypeError("param seed should be of type str")
    elif type(width) != int:
        raise TypeError("param width should be of type int")
    elif type(pad) != float or pad > 1.0:
        raise TypeError("param pad should be of type float <= 1.0")

    seed = sha1(seed.encode()).hexdigest()[:15]

    b, p = width // 5, width * pad
    w = int(b * 5 + 2 * p)

    # first character used for the luminosity
    luminosity = 50
    if int(seed[0], 16) % 2 == 0:
        luminosity += 18

    # first 5 characters used for the hue
    hue = int(seed[:5], 16) / 0xFFFFF * 360
    hsl = "hsl(%d, 80%%, %d%%)" % (hue, luminosity)

    image = Image.new("RGB", (w, w), hsl)
    colored = []

    for i, v in enumerate(seed):
        yes = ord(v) % 2 != 0
        colored.append(yes)

        if yes and i < 10:
            _square(image, i // 5, i % 5, b, p)
            _square(image, 4 - i // 5, i % 5, b, p)
        elif yes:
            _square(image, i // 5, i - 10, b, p)

    # langweilig sprites
    if all(colored) or not any(colored):
        return generate_identicon(seed, b, p)

    return image
