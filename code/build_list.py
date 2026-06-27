import copy
import glob
import json
from copy import deepcopy
from typing import Union

import imagehash
from cloudflare.types.kv.namespaces import ValueUpdateResponse

from hamming import hamming_distance
from PIL import Image
import os
from cloudflare import Cloudflare


# Generates a list of hashes based on a folder "scam_images" with a list of folders containing images within it.


def get_phash_and_dimensions(filename: str) -> tuple[str, tuple]:
    phash: str = ""
    dimensions: tuple[int, int] = (0,0)
    try:
        img = Image.open(filename)
        phash = str(imagehash.phash(img, hash_size=16))
        dimensions = img.size
    finally:
        return phash, dimensions


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

def get_filenames() -> list[str]:
    return glob.glob(r"../*/*")

def get_hashes() -> list[str]:
    hashes: list = []
    for target in get_filenames():  # Build list
        phash, _ = get_phash_and_dimensions(target)
        if phash:
            hashes.append(phash)
    return hashes

def get_hashes_and_dimensions() -> list[dict]:
    hashes_and_dimensions: list[dict] = []
    for target in get_filenames():  # Build list
        phash, dimensions = get_phash_and_dimensions(target)
        if phash and dimensions != (0,0):
            hashes_and_dimensions.append({"phash": phash, "dimensions": dimensions})
    return hashes_and_dimensions


def main() -> None:
    hashes: list = get_hashes()
    hashes_and_dimensions: list[dict] = get_hashes_and_dimensions()
    hashes_and_dimensions_temp = []
    print(f"Pre-dupe-removal:   {len(hashes_and_dimensions)}")
    for hash in hashes_and_dimensions:
        if hash in hashes_and_dimensions_temp:
            continue
        hashes_and_dimensions_temp.append(hash)
    hashes_and_dimensions = hashes_and_dimensions_temp
    print(f"Post-dupe-removal:  {len(hashes_and_dimensions)}")
    hashes_and_dimensions_string: str = json.dumps(hashes_and_dimensions, ensure_ascii=False, indent=None)
    print(f"hashes_and_dimensions: {hashes_and_dimensions_string}")
    hashes.sort()
    print(f"Pre-dupe-removal:   {len(hashes)}")
    hashes = list(set(hashes))  # Remove dupes
    hashes.sort()
    print(f"Post-dupe-removal:  {len(hashes)}")
    hashes = rem_collisions(hashes) # Remove collisions < 4 hamming distance
    hashes.sort()
    print(f"Post-hamming-clear: {len(hashes)}")
    hash_string = json.dumps(hashes, ensure_ascii=False, indent=None)
    print(f'{hash_string}')
    hashes.sort()
    try:
        with open("../hashes.json", "r") as hash_file:
            old_hashes = json.load(hash_file)
        old_hash_string = json.dumps(old_hashes, ensure_ascii=False, indent=None)
        print(f"Old hashes\nCount: {len(old_hashes)} List: [\"{old_hash_string}\"]")
        print(f"New hashes\nCount: {len(hashes)} List: {hash_string}")
    except OSError:
        old_hashes = []
    finally:
        with open("../hashes.json", "w") as hash_file:
            json.dump(hashes, hash_file, ensure_ascii=False, indent=4)
    try:
        with open("../hashes_and_dimensions.json", "r") as hash_file:
            old_hashes_and_dimensions = json.load(hash_file)
        old_hashes_and_dimensions_string = json.dumps(old_hashes_and_dimensions, ensure_ascii=False, indent=None)
        print(f"Old old_hashes_and_dimensions\nCount: {len(old_hashes_and_dimensions)} List: {old_hashes_and_dimensions_string}")
        print(f"New old_hashes_and_dimensions\nCount: {len(hashes_and_dimensions)} List: {hashes_and_dimensions_string}")
    except OSError:
        old_hashes_and_dimensions = []
    finally:
        with open("../hashes_and_dimensions.json", "w") as hash_file:
            json.dump(hashes_and_dimensions, hash_file, ensure_ascii=False, indent=4)
    if not os.path.exists("../.kv_config.json"):
        print("No .kv_config.json file")
        return
    with open("../.kv_config.json", "r") as kv_config_file:
        kv_config = json.load(kv_config_file)
    client = Cloudflare(api_token=kv_config["CLOUDFLARE_API_TOKEN"])
    response_a = False
    response_b = False
    if len(old_hashes) < len(hashes):
        response_a = update_phash(client=client, kv_config=kv_config, hash_string=hash_string)
    else:
        print("Hash list same or smaller.")
    if len(old_hashes_and_dimensions) < len(hashes_and_dimensions):
        response_b = update_phash_and_dimensions(client=client, kv_config=kv_config, hashes_and_dimensions_string=hashes_and_dimensions_string)
    else:
        print("Hash and dimensions list same or smaller.")

    if response_a:
        print(f"Response: {response_a}")
    elif response_a is None:
        print("Cloudflare kv updated for hash list!")
    if response_b:
        print(f"Response: {response_b}")
    elif response_b is None:
        print("Cloudflare kv updated for hash and dimension list!")

def update_phash(client: Cloudflare, kv_config: dict, hash_string: str) -> Union[str, None, ValueUpdateResponse]:
    if not hash_string:
        print("No hash string")
        return "Not updated"
    return client.kv.namespaces.values.update(key_name=kv_config["KV_PAIR1"], namespace_id=kv_config["NAMESPACE_ID"], value=hash_string.encode('utf-8'), account_id=kv_config["ACCOUNT_ID"])

def update_phash_and_dimensions(client: Cloudflare, kv_config: dict, hashes_and_dimensions_string: str) -> Union[str, None, ValueUpdateResponse]:
    if not hashes_and_dimensions_string:
        print("No hashes and dimensions string")
        return "Not updated"
    return client.kv.namespaces.values.update(key_name=kv_config["KV_PAIR2"], namespace_id=kv_config["NAMESPACE_ID"], value=hashes_and_dimensions_string.encode('utf-8'), account_id=kv_config["ACCOUNT_ID"])


if __name__ == "__main__":
    main()
