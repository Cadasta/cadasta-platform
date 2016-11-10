from PIL import Image


def is_landscape(width, height):
    if width >= height:
        return True
    else:
        return False


def box_params_center(width, height):
    if is_landscape(width, height):
        upper_x = int((width/2) - (height/2))
        upper_y = 0
        lower_x = int((width/2) + (height/2))
        lower_y = height
        return upper_x, upper_y, lower_x, lower_y
    else:
        upper_x = 0
        upper_y = int((height/2) - (width/2))
        lower_x = width
        lower_y = int((height/2) + (width/2))
        return (upper_x, upper_y, lower_x, lower_y)


def crop(img):
    box = box_params_center(img.size[0], img.size[1])
    region = img.crop(box)
    return region


def make(img, size):
    im = fix_orientation(Image.open(img))
    copy = im.copy()
    cropped_img = crop(copy)
    cropped_img.thumbnail(size, Image.ANTIALIAS)
    return cropped_img


# Code below this point is adapted from
#
#  https://github.com/kylefox/python-image-orientation-patch
#
# licensed under the following license:
#
# The MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# The EXIF tag that holds orientation data.
EXIF_ORIENTATION_TAG = 274

# Obviously the only ones to process are 3, 6 and 8.
# All are documented here for thoroughness.
ORIENTATIONS = {
    1: ("Normal", 0),
    2: ("Mirrored left-to-right", 0),
    3: ("Rotated 180 degrees", 180),
    4: ("Mirrored top-to-bottom", 0),
    5: ("Mirrored along top-left diagonal", 0),
    6: ("Rotated 90 degrees", -90),
    7: ("Mirrored along top-right diagonal", 0),
    8: ("Rotated 270 degrees", -270)
}


def fix_orientation(img):
    try:
        orientation = img._getexif()[EXIF_ORIENTATION_TAG]
    except (TypeError, AttributeError, KeyError):
        return img
    if orientation in [3, 6, 8]:
        degrees = ORIENTATIONS[orientation][1]
        img = img.rotate(degrees)
        return img
    else:
        return img
