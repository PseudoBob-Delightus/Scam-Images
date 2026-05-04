import imagehash
from PIL import Image
# Generating a pHash using imagehash library and PIL


def get_phash(filename: str) -> str:    
    img = Image.open(filename)
    return str(imagehash.phash(img, hash_size=16))  # I find this size hash gives more granularity, YMMV
