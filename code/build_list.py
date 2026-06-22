import glob
import json
from copy import deepcopy

import imagehash

from hamming import hamming_distance
from PIL import Image
import os
from cloudflare import Cloudflare


# Generates a list of hashes based on a folder "scam_images" with a list of folders containing images within it.


def get_phash(filename: str) -> str:
    phash: str = ""
    try:
        img = Image.open(filename)
        phash = str(imagehash.phash(img, hash_size=16))
    finally:
        return phash


def rem_collisions(hashes: list[str]) -> list[str]:
    """
    takes a list of hashes (str) and removes collisions (distance < 4)
    returns a list[str]
    """
    hash1: str
    hash2: str
    for hash1 in deepcopy(hashes):
        for hash2 in deepcopy(hashes):
            if hash1 == hash2:
                continue
            if hamming_distance(hash1, hash2) < 4:
                hashes.remove(hash1)
                break
    return hashes


def get_hashes() -> list[str]:
    file_list = glob.glob(r"../*/*")
    hashes: list = []
    for target in file_list:  # Build list
        if phash := get_phash(target):
            hashes.append(phash)
    return hashes


def main() -> None:
    hashes: list = get_hashes()
    hashes.sort()
    print(f"Pre-dupe-removal:   {len(hashes)}")
    hashes = list(set(hashes))  # Remove dupes
    hashes.sort()
    print(f"Post-dupe-removal:  {len(hashes)}")
    hashes = rem_collisions(hashes) # Remove collisions < 4 hamming distance
    hashes.sort()
    print(f"Post-hamming-clear: {len(hashes)}")
    hash_string = '","'.join(hashes)
    print(f'["{hash_string}"]')
    hash_string = f'["{hash_string}"]'
    hashes.sort()
    try:
        with open("../hashes.json", "r") as hash_file:
            old_hashes = json.load(hash_file)
        old_hash_string = '","'.join(old_hashes)
        print(f"Old hashes\nCount: {len(old_hashes)}\nList: [\"{old_hash_string}\"]")
        print(f"New hashes\nCount: {len(hashes)}\nList: {hash_string}")
    except OSError:
        old_hashes = []
    with open("../hashes.json", "w") as hash_file:
        json.dump(hashes, hash_file, ensure_ascii=False, indent=4)
    if not os.path.exists("../.kv_config.json"):
        print("No .kv_config.json file")
        return
    if not hash_string:
        print("No hash string")
        return
    if len(old_hashes) >= len(hashes):
        print("Hash string is same or smaller.")
        return
    with open("../.kv_config.json", "r") as kv_config_file:
        kv_config = json.load(kv_config_file)
    client = Cloudflare(api_token=kv_config["CLOUDFLARE_API_TOKEN"])
    response = client.kv.namespaces.values.update(key_name=kv_config["KV_PAIR"], namespace_id=kv_config["NAMESPACE_ID"], value=hash_string.encode('utf-8'), account_id=kv_config["ACCOUNT_ID"])
    print("Cloudflare kv updated!")
    if response:
        print(f"Response: {response}")


if __name__ == "__main__":
    main()
