from PIL import Image

def make_blank(width=860, height=1200):
    image = Image.new("RGB", (width, height), "white")
    return image
