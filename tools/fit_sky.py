#!/usr/bin/env python3
"""
Fit a handful of soft "globs" to the dusk sky.

Target: the sky model measured from the reference photograph (a row-by-row vertical gradient plus a
left-to-right tint that wraps smoothly round the back), evaluated over the WHOLE sphere of directions.
Model:  colour = base + haze(y) + sum_i  strength_i * offset_i * exp(-(1 - cos(theta_i)) / sigma_i^2)
        haze(y) = sum_k bandcolour_k * exp(-y / eps_k)   (y = sin(elevation): thin dark bands hugging the horizon, fixed in place)
        theta_i = angle between the view direction and glob i's centre (for small angles a gaussian of std sigma_i).
        Each glob adds a signed colour offset: a warm glow where it is positive, a cool shadow where it is negative.
Because the model is LINEAR in (base, offsets), the colours are solved exactly (ridge-regularised) for any placement
of the globs, and only the placement (azimuth, elevation, size) is searched nonlinearly: "variable projection".
The result is written to tools/sky_blobs.json and pasted into index.html as the initial condition (t = 0).

    python3 tools/fit_sky.py [N_BLOBS] [N_RESTARTS] [RIDGE]
"""
import json, sys, numpy as np
from scipy.optimize import least_squares

F = (605 / 2) / np.tan(np.radians(15))                      # focal length in reference pixels
HORIZON_Y = 460
STOPS = sorted([(HORIZON_Y - y, c) for y, *c in [(0,106,81,91),(120,101,76,88),(240,92,68,86),(300,83,62,82),(360,70,55,78),(420,55,48,71),(440,40,37,58),(460,33,31,50)]], key=lambda s: s[0])
SH = np.array([s[0] for s in STOPS], float); SC = np.array([s[1] for s in STOPS], float)
TX = np.array([0,180,360,540,720,900,1080], float)
TD = np.array([[-6,-12,-11],[-2,-1,-2],[1,1,0],[0,0,0],[-15,-7,-7],[-30,-8,-10],[-40,-9,-11]], float)

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def target(az, el):
    """The existing sky (sRGB bytes) for directions (azimuth, elevation) in radians. az = 0 is straight ahead, + is to the right."""
    h = F * np.tan(el)
    grad = np.stack([np.interp(h, SH, SC[:, k]) for k in range(3)], -1)
    aR = np.arctan(540 / F)
    x = 540 + F * np.tan(np.clip(az, -aR, aR))
    inner = np.stack([np.interp(x, TX, TD[:, k]) for k in range(3)], -1)
    span = 2 * np.pi - 2 * aR
    tt = np.where(az > 0, az - aR, az + 2 * np.pi - aR) / span
    s = (tt * tt * (3 - 2 * tt))[..., None]
    outer = TD[6] * (1 - s) + TD[0] * s
    tint = np.where((np.abs(az) <= aR)[..., None], inner, outer)
    return grad + tint * smoothstep(0, 160, h)[..., None]

def directions(az, el):
    return np.stack([np.sin(az) * np.cos(el), np.sin(el), -np.cos(az) * np.cos(el)], -1)   # +x right, +y up, -z ahead

EPS = [0.012, 0.04]                                         # horizon haze scales, in y = sin(elevation)

def basis(geo, n, d):
    """geo = [az, el, log sigma] * n  ->  (samples, n) glob falloffs"""
    cols = []
    for i in range(n):
        az, el, ls = geo[3 * i: 3 * i + 3]
        c = directions(np.array(az), np.array(el))
        cols.append(np.exp((np.clip(d @ c, -1, 1) - 1) / np.exp(ls) ** 2))
    return np.stack(cols, -1)

def solve(geo, n, d, T, w, ridge):
    """Best base + offsets for this placement (weighted, ridge-regularised on the offsets). Returns (coefs (n+1, 3), predictions)."""
    G = basis(geo, n, d).reshape(-1, n)
    H = np.stack([np.exp(-d[..., 1] / e) for e in EPS], -1).reshape(-1, len(EPS))
    A = np.concatenate([np.ones((G.shape[0], 1)), H, G], 1); K = 1 + len(EPS)
    W = np.sqrt(w.reshape(-1, 1)); y = T.reshape(-1, 3)
    R = np.sqrt(ridge) * np.eye(n + K); R[:K, :K] = 0
    lhs = np.concatenate([A * W, R]); rhs = np.concatenate([y * W, np.zeros((n + K, 3))])
    coef = np.linalg.lstsq(lhs, rhs, rcond=None)[0]
    return coef, (A @ coef).reshape(d.shape[:-1] + (3,))

def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    R = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    ridge = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
    az = np.radians(np.arange(-180, 180, 4.0)); el = np.radians(np.arange(0, 82, 2.0))
    AZ, EL = np.meshgrid(az, el, indexing='ij')
    D = directions(AZ, EL); T = target(AZ, EL)
    # weights: the visible frame (±26° either side of ahead) and the low sky matter most; the zenith and the back least
    w = (1 + 3 * (np.abs(AZ) < np.radians(30)) + 1.5 * (EL < np.radians(30)))
    lo = [-np.pi, 0.0, np.log(0.16)] * N; hi = [np.pi, 1.45, np.log(1.2)] * N
    rng = np.random.default_rng(11); best = None
    def res(geo):
        _, pred = solve(geo, N, D, T, w, ridge)
        return ((pred - T) / 255 * np.sqrt(w)[..., None]).ravel()
    for k in range(R):
        g0 = []
        for i in range(N): g0 += [rng.uniform(-np.pi, np.pi), rng.uniform(0.05, 1.3), np.log(rng.uniform(0.2, 0.7))]
        r = least_squares(res, np.clip(g0, lo, hi), bounds=(lo, hi), max_nfev=60)
        coef, pred = solve(r.x, N, D, T, w, ridge)
        rms = np.sqrt(np.mean((pred - T) ** 2))
        if best is None or rms < best[0]: best = (rms, r.x, coef); print(f"restart {k:2d}: RMS {rms:.3f} bytes (best {best[0]:.3f})", flush=True)
    rms, geo, coef = best
    _, pred = solve(geo, N, D, T, w, ridge); err = pred - T
    fr = np.abs(AZ) < np.radians(26)
    print(f"\nN={N} ridge={ridge}  overall RMS {rms:.2f} bytes | visible-frame RMS {np.sqrt(np.mean(err[fr] ** 2)):.2f} | max abs error {np.abs(err).max():.1f}   (film grain std is ~9 bytes)")
    K = 1 + len(EPS); order = np.argsort(-np.abs(coef[K:]).sum(1))
    out = {"n": N, "model": "additive", "base": [round(float(v), 2) for v in coef[0]],
           "haze": [{"eps": e, "color": [round(float(v), 1) for v in coef[1 + k]]} for k, e in enumerate(EPS)], "blobs": []}
    for i in order:
        az_, el_, ls = geo[3 * i: 3 * i + 3]
        out["blobs"].append({"az": round(float(az_), 4), "el": round(float(el_), 4), "sigma": round(float(np.exp(ls)), 4), "color": [round(float(v), 1) for v in coef[K + i]]})
    out["rms_bytes"] = round(float(rms), 3); out["frame_rms_bytes"] = round(float(np.sqrt(np.mean(err[fr] ** 2))), 3); out["max_abs_error"] = round(float(np.abs(err).max()), 1)
    json.dump(out, open("tools/sky_blobs.json", "w"), indent=1)
    print("glob offset magnitudes (bytes):", [round(float(np.abs(b["color"]).max()), 1) for b in out["blobs"]]); print("haze:", out["haze"], "base:", out["base"])

main()
