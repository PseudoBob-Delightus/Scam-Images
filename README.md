# Scam-Images
A list of images that are known scams that get posted to chat services. Please treat these like Co-60 and don't share them on rando servers. Drop and run!

I accept PRs with new images. Please use the format (d/m/yyyy) for the folder and make an `info.txt` file to state where you found them.

Can recommend using something like [ImageHash (python)](https://pypi.org/project/ImageHash/) for comparing images. A hamming distance of ~4 should account for JPG compression without catching unrelated things.

If you lack the ability to post a PR, please send the images to: spam-images@excessive.space

An API endpoint has been set up: `https://api.excessive.space/v1/hashcompare?hash=<64char_hash>`

This will return json with either a `result` or `error` key. 

A `result` of `true` indicates a match to within 4 hamming distance of a scam image. `false` indicates it is outside this range.

An `error` (and a 400 response) will explain what was wrong.

Using the test image: https://api.excessive.space/v1/hashcompare?hash=bbac1388cc534c6133166616c8f9d0193e6c36e5d3072f9994f9ccf63f823336

Will return a 200: 
```
{
  "result": true
}
```

Using an altered (non-matching) hash: https://api.excessive.space/v1/hashcompare?hash=bbac1388cc534c6133166616c8f9d0193e6c36e5d3072f9994f9ccf63f823300

Will return a 404:
```
{
  "result": false
}
```

<img width="500" height="auto" alt="image" src="https://github.com/user-attachments/assets/c9906e97-127f-4928-b8d0-bd39fa867c55" />


Projects using this data:
- https://github.com/SomewhatDamaged/SentryBot
- https://github.com/SomewhatDamaged/hashcompare
