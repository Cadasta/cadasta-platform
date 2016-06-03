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
    im = Image.open(img)
    copy = im.copy()
    cropped_img = crop(copy)
    cropped_img.thumbnail(size, Image.ANTIALIAS)
    return cropped_img
