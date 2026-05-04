import glob
import json
from copy import deepcopy

import imagehash
from hamming import hamming_distance
from PIL import Image

# Generates a list of hashes based on a folder "scam_images" with a list of folders containing images within it.


def get_phash(filename: str) -> str:
    output = ""
    try:
        img = Image.open(filename)
        output = str(imagehash.phash(img, hash_size=16))
    finally:
        return output


def main() -> None:
    hashes = []
    list_ = glob.glob(r"./*/*")
    print(list_)
    for target in list_:  # Build list
        if phash := get_phash(target):
            hashes.append(phash)
    print(f"Pre-dupe-removal:   {len(hashes)}")
    hashes = list(set(hashes))  # Remove dupes
    print(f"Post-dupe-removal:  {len(hashes)}")
    for hash1 in deepcopy(hashes):
        for hash2 in deepcopy(hashes):
            if hash1 == hash2:
                continue
            if hamming_distance(hash1, hash2) < 4:
                hashes.remove(hash1)
                break
    print(f"Post-hamming-clear: {len(hashes)}")
    hash_string = '","'.join(hashes)
    print(f'["{hash_string}"]')
    with open("hashes.json", "w") as hash_file:
        json.dump(hashes, hash_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
