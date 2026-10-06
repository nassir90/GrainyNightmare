# Dependencies

GrainyNightmare has no build step and almost no dependencies. Versions and dates checked 6 October 2026.

## What the project uses today

| Dependency | Version used | Latest | Where | Notes |
|---|---|---|---|---|
| [three.js](https://github.com/mrdoob/three.js) | **0.170.0** | 0.186.1 (Sep 2026) | `index.html`, via an import map from jsDelivr | The only runtime dependency. Pinned in the import map. |
| three `BufferGeometryUtils` addon | 0.170.0 | (ships with three) | `index.html` (`mergeGeometries`) | Same package as above. |
| [Cloudflare Wrangler](https://github.com/cloudflare/workers-sdk) | **4.148.0** | 4.148.0 (Oct 2026) | `worker/deploy.sh`, run with `npx` | Deploy only. Now pinned; it was `@latest`. |
| [NumPy](https://numpy.org) | 2.0.2 | (n/a) | `tools/fit_sky.py` | Sky fitting only (`tools/requirements.txt`). |
| [SciPy](https://scipy.org) | 1.13.1 | (n/a) | `tools/fit_sky.py` (`least_squares`) | Sky fitting only. |
| Python | 3.9+ | (n/a) | `tools/*.py` | Sky fitting only. |

Browser features relied on: WebGL 2 (half-float multisampled render targets), ES modules and import maps, Pointer Events, `matchMedia('(pointer: coarse)')`, `env(safe-area-inset-*)`.

**Upgrading three.js** from 0.170 to 0.186 is likely straightforward. The page uses only core APIs: `ShaderMaterial`, `onBeforeCompile` patches of the standard material (`#include <opaque_fragment>`, `<begin_vertex>`, `<common>`), and the colour-space functions three prepends to shaders. Those `onBeforeCompile` string replacements are the part most likely to break between versions, so re-check that every scene renders after an upgrade.

## Things we wrote by hand, and what already exists

| What we have | Existing, maintained alternative | Status |
|---|---|---|
| GLSL sRGB ↔ linear conversion (two hand-written copies) | three's `sRGBTransferEOTF` / `sRGBTransferOETF`, prepended to every `ShaderMaterial` | **Adopted.** Our copies are deleted. |
| Exponential smoothing `x += (target − x)·(1 − e^(−dt/τ))`, written out in 8 places | `THREE.MathUtils.damp` (built in) | **Adopted** through one `smooth()` wrapper. |
| Seeded random number generator for the sky (an LCG) | `THREE.MathUtils.seededRandom` (Mulberry32, built in); [`pure-rand`](https://github.com/dubzzz/pure-rand) 8.4.2 (Jul 2026) | **Suggested, not done.** Switching changes which sky every existing `?seed=…` link shows. |
| Bloom chain: bright pass, 4-level ping-pong gaussian blur, fullscreen-quad plumbing (~45 lines) | [`postprocessing`](https://github.com/pmndrs/postprocessing) 6.39.5 (Sep 2026): `EffectComposer` + `BloomEffect` (mipmap blur, luminance threshold); or three's own `EffectComposer` + `UnrealBloomPass` addons | **Suggested.** Worth adopting if the post pipeline grows. The grain warp would become a custom `Effect` that reads the scene's alpha (distance) channel. |
| Critically damped spring (camera lag, 6 lines) | [`maath`](https://github.com/pmndrs/maath) 0.10.8 (Aug 2026): `easing.damp` / `damp3` | **Keep.** It's tiny, exact and frame-rate independent. Adopt maath only if more springs or easings appear. |
| GLSL hash and value noise (film grain) | [`lygia`](https://github.com/patriciogonzalezvivo/lygia) 1.4.1 (Feb 2026): `generative/random`, `generative/noise` | **Keep.** lygia needs an include resolver, so it doesn't fit a no-build single file. |
| Floating touch joystick (~35 lines) | [`nipplejs`](https://github.com/yoannmoinet/nipplejs) 1.0.4 (May 2026) | **Keep.** Ours is styled to match and does nothing extra. Consider nipplejs if more touch controls are needed. |
| Wobbling line sliders (canvas) | [`lil-gui`](https://github.com/georgealways/lil-gui) 0.21 (Oct 2025), [`Tweakpane`](https://github.com/cocopon/tweakpane) 4.0.5 (Nov 2024, slower lately) | **Keep** for the visible HUD, since its look is the point. Either library is a good drop-in for a hidden debug panel. |
| Sky gradient model | three's `Sky` addon (Preetham daylight) | **Not a fit.** It's a physical daylight model, and ours is a fitted, drifting dusk. |
| First-person controls | three's `PointerLockControls` / `FirstPersonControls` addons | **Keep.** Ours also covers touch (joystick plus look-drag) and the eased handoff from the fixed view. |
| Lattice-beam, catenary-wire, airfoil-blade and instanced-grass geometry | No maintained library covers these | **Keep.** |
