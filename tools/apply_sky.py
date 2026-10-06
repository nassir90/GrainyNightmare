#!/usr/bin/env python3
"""Write the fit in tools/sky_blobs.json into index.html as the sky's t = 0 state (the `const SKY_INIT = {...};` line).

    python3 tools/fit_sky.py && python3 tools/apply_sky.py
"""
import json, re

fit = json.load(open('tools/sky_blobs.json'))
init = json.dumps({"base": fit["base"], "haze": fit["haze"],
                   "blobs": [{k: b[k] for k in ("az", "el", "sigma", "color")} for b in fit["blobs"]]}, separators=(',', ':'))
s = open('index.html').read()
s, n = re.subn(r"^const SKY_INIT = .*;$", lambda _: f"const SKY_INIT = {init};", s, count=1, flags=re.M)
assert n == 1, "could not find the `const SKY_INIT = ...;` line in index.html"
open('index.html', 'w').write(s)
print(f"applied: {len(fit['blobs'])} globs, {len(fit['haze'])} haze bands, fit RMS {fit['rms_bytes']} bytes (visible frame {fit['frame_rms_bytes']})")
