import glob
import json
from copy import deepcopy
from typing import Union

import imagehash
from cloudflare.types.kv.namespaces import ValueUpdateResponse
import io

from split_images import split_two_images
from hamming import hamming_distance
from PIL import Image
import os
from cloudflare import Cloudflare


# Generates a list of hashes based on a folder "scam_images" with a list of folders containing images within it.


def get_phash_and_dimensions(filename: str) -> list[tuple[str, tuple]]:
    phash: str = ""
    dimensions: tuple[int, int] = (0,0)
    output: list[tuple[str, tuple]] = []
    try:
        img = Image.open(filename)
        image = io.BytesIO()
        img.save(image, format="PNG")
        images = split_two_images(image)
        for image in images:
            phash = str(imagehash.phash(Image.open(image), hash_size=16))
            dimensions = img.size
            output.append((phash, dimensions))
    finally:
        return output


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
        result = get_phash_and_dimensions(target)
        for phash, _ in result:
            if phash:
                hashes.append(phash)
    return hashes

def get_hashes_and_dimensions() -> list[dict]:
    hashes_and_dimensions: list[dict] = []
    for target in get_filenames():  # Build list
        result = get_phash_and_dimensions(target)
        for phash, dimensions in result:
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
        print(f"Old hashes\nCount: {len(old_hashes)} List: {old_hash_string}")
        print(f"New hashes\nCount: {len(hashes)} List: {hash_string}")
    except OSError:
        old_hashes = []
        old_hash_string = ""
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
        old_hashes_and_dimensions_string = ""
    finally:
        with open("../hashes_and_dimensions.json", "w") as hash_file:
            json.dump(hashes_and_dimensions, hash_file, ensure_ascii=False, indent=4)
    if not os.path.exists("../.kv_config.json"):
        print("No .kv_config.json file")
        return
    with open("../.kv_config.json", "r") as kv_config_file:
        kv_config = json.load(kv_config_file)
    client = Cloudflare(api_token=kv_config["CLOUDFLARE_API_TOKEN"])
    response_a1 = None
    response_b1 = None
    response_a2 = ""
    response_b2 = ""
    if len(old_hashes) < len(hashes):
        if old_hash_string:
            response_a1 = update_phash(client=client, kv_config=kv_config, hash_string=old_hash_string, backup=True)
        else:
            response_a1 = None
        response_a2 = update_phash(client=client, kv_config=kv_config, hash_string=hash_string)
    else:
        print("Hash list same or smaller.")
    if len(old_hashes_and_dimensions) < len(hashes_and_dimensions):
        if old_hashes_and_dimensions_string:
            response_b1 = update_phash_and_dimensions(client=client, kv_config=kv_config, hashes_and_dimensions_string=old_hashes_and_dimensions_string, backup=True)
        else:
            response_b1 = None
        response_b2 = update_phash_and_dimensions(client=client, kv_config=kv_config, hashes_and_dimensions_string=hashes_and_dimensions_string)
    else:
        print("Hash and dimensions list same or smaller.")

    if response_a1:
        print(f"Response: \n{response_a1}")
    elif response_a2 is None:
        print("Cloudflare kv updated for hash list!")
    if response_a2:
        print(f"Response: \n{response_a2}")
    if response_b1:
        print(f"Response: \n{response_b1}")
    elif response_b2 is None:
        print("Cloudflare kv updated for hash and dimension list!")
    if response_b2:
        print(f"Response: \n{response_b2}")

def update_phash(client: Cloudflare, kv_config: dict, hash_string: str, backup: bool = False) -> Union[str, None, ValueUpdateResponse]:
    if not hash_string:
        print("No hash string")
        return "Not updated"
    if not backup:
        return client.kv.namespaces.values.update(key_name=kv_config["KV_PAIR1"],
                                                  namespace_id=kv_config["NAMESPACE_ID"],
                                                  value=hash_string.encode('utf-8'),
                                                  account_id=kv_config["ACCOUNT_ID"])
    else:
        return client.kv.namespaces.values.update(key_name=kv_config["KV_PAIR1"] + "_backup",
                                                  namespace_id=kv_config["NAMESPACE_ID"],
                                                  value=hash_string.encode('utf-8'),
                                                  account_id=kv_config["ACCOUNT_ID"])

def update_phash_and_dimensions(client: Cloudflare, kv_config: dict, hashes_and_dimensions_string: str, backup: bool = False) -> Union[str, None, ValueUpdateResponse]:
    if not hashes_and_dimensions_string:
        print("No hashes and dimensions string")
        return "Not updated"
    if not backup:
        return client.kv.namespaces.values.update(key_name=kv_config["KV_PAIR2"],
                                                  namespace_id=kv_config["NAMESPACE_ID"],
                                                  value=hashes_and_dimensions_string.encode('utf-8'),
                                                  account_id=kv_config["ACCOUNT_ID"])
    else:
        return client.kv.namespaces.values.update(key_name=kv_config["KV_PAIR2"] + "_backup",
                                                  namespace_id=kv_config["NAMESPACE_ID"],
                                                  value=hashes_and_dimensions_string.encode('utf-8'),
                                                  account_id=kv_config["ACCOUNT_ID"])


if __name__ == "__main__":
    main()
