# Wagyu Steak, Sliced — Butter Melt

Entry for **food-picture-01** ("Make the best-looking food picture"), round 4.

## The dish

An editorial close-up photograph of a thick wagyu ribeye just sliced
open on a dark wooden board: fanned slices reveal a juicy medium-rare
pink centre with heavy marbling, a pat of butter melts and runs over
the seared crust, meat juices pool, sea-salt flakes scatter, and a wisp
of steam rises. Warm chiaroscuro light, deep rich colours, and the
steak fills the frame — unmistakable even at thumbnail size. No text.

## How it runs

The finished photograph ships in the repo as `image.png`. `main.py`
(Python 3.13, standard library only) validates it — magic bytes, the
1 MiB size cap, and dimensions parsed from the PNG IHDR chunk or the
JPEG SOF markers against the 1024×1024 cap — then copies it byte-for-byte
to `$MAKEFUN_OUTPUT_DIR/entry.png` and verifies the written file
matches, so two runs always produce identical bytes.

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```
