#!/usr/bin/env python3
"""Swap the gradient-texture sky in index.html for the glob sky, using the fit in tools/sky_blobs.json as the t = 0 initial condition."""
import json, re
fit = json.load(open('tools/sky_blobs.json'))
init = json.dumps({"base": fit["base"], "haze": fit["haze"], "blobs": [{"az": b["az"], "el": b["el"], "sigma": b["sigma"], "color": b["color"]} for b in fit["blobs"]]}, separators=(',', ':'))
s = open('index.html').read()
def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b, 1)

# 1. the old measured tables are no longer used at run time (they live on as the fitting target in tools/fit_sky.py)
i = s.index("// [y px in ref, r, g, b] — mean of the brighter 40% of pixels per row"); j = s.index("const GROUND = ")
s = s[:i] + "// The sky itself is a set of drifting globs (see \"Sky\" below). Its t = 0 state was fitted, by tools/fit_sky.py, to the gradient measured\n// from the reference photograph: row-by-row means of the brighter 40% of pixels (silhouettes excluded), plus a left-to-right tint.\n\n" + s[j:]

# 2. the sky dome
i = s.index("/* ------------------------------------------------------------------ *\n *  Sky dome:"); j = s.index("scene.add(sky);") + len("scene.add(sky);")
sky = r'''/* ------------------------------------------------------------------ *
 *  Sky: soft globs drifting over a base colour, above a thin band of horizon haze. The globs wander, breathe and shift colour,
 *  so the sky evolves. Its t = 0 state (SKY_INIT) was fitted to the reference gradient by tools/fit_sky.py.
 *    colour = base + Σ haze.colour · e^(−y/ε)  +  Σ strength · glob.offset · e^(−(1 − cos θ)/σ²)
 *    (y = sin(elevation); θ = angle from a glob's centre, so each glob is ≈ a gaussian of std σ; offsets are signed: glows and shadows)
 * ------------------------------------------------------------------ */
const SKY_INIT = ''' + init + r''';
const SKY_N = SKY_INIT.blobs.length, HAZE_N = SKY_INIT.haze.length;
// Each glob gets its own deterministic motion (seeded, so every load evolves the same way): the sky is a pure function of time.
// Every load starts somewhere new: a random seed picks each glob's motion, and a random start time (1–10 min) picks how far it has
// already drifted, so each visit opens on a different (but always naturally evolved) dusk.
//   ?sky=fitted      the fitted state itself (the parity screenshots)      ?seed=N&t=S   pin one particular sky (shareable)
const skyQ = new URLSearchParams(location.search), SKY_FITTED = skyQ.get('sky') === 'fitted';
const SKY_SEED = SKY_FITTED ? 20260506 : ((+skyQ.get('seed') >>> 0) || ((Math.random() * 4294967296) >>> 0));
const skyRand = (() => { let q = SKY_SEED; return () => (q = (q * 1664525 + 1013904223) >>> 0) / 4294967296; })();
const SKY_MOTION = SKY_INIT.blobs.map(() => ({
  w: (skyRand() < 0.5 ? -1 : 1) * (0.003 + skyRand() * 0.009),                         // steady drift round the sky, rad/s (0.2–0.7°/s)
  az: [0.05 + skyRand() * 0.12, 0.015 + skyRand() * 0.03, skyRand() * 6.283],           // azimuth wobble: amplitude (rad), rate (rad/s), phase
  el: [0.08 + skyRand() * 0.16, 0.012 + skyRand() * 0.03, skyRand() * 6.283],           // rising and sinking
  size: [0.15 + skyRand() * 0.2, 0.01 + skyRand() * 0.03, skyRand() * 6.283],           // breathing (fraction of σ)
  str: [0.2 + skyRand() * 0.25, 0.01 + skyRand() * 0.03, skyRand() * 6.283],            // swelling and fading (fraction of strength)
  hue: [0, 1, 2].map(() => [4 + skyRand() * 8, 0.008 + skyRand() * 0.025, skyRand() * 6.283]),   // per-channel colour drift, bytes
}));
const HAZE_MOTION = SKY_INIT.haze.map(() => [0.15 + skyRand() * 0.15, 0.006 + skyRand() * 0.01, skyRand() * 6.283]);   // the haze thickens and thins
const osc = ([A, n, p], t) => A * (Math.sin(n * t + p) - Math.sin(p));                     // zero at t = 0, so the fitted state is exact
const skyU = {
  uBase: { value: new THREE.Vector3() },
  uHaze: { value: Array.from({ length: HAZE_N }, () => new THREE.Vector4()) },             // (offset rgb, ε)
  uBlobPos: { value: Array.from({ length: SKY_N }, () => new THREE.Vector3()) },
  uBlobCol: { value: Array.from({ length: SKY_N }, () => new THREE.Vector3()) },          // signed offset, 0..1 units
  uBlobK: { value: new Array(SKY_N).fill(1) },                                              // 1/σ²
};
const clampN = THREE.MathUtils.clamp;
function applySky(t) {
  const b0 = SKY_INIT.base;
  skyU.uBase.value.set((b0[0] + osc([5, 0.011, 1.3], t)) / 255, (b0[1] + osc([4, 0.013, 2.1], t)) / 255, (b0[2] + osc([5, 0.009, 4.0], t)) / 255);
  SKY_INIT.haze.forEach((hz, k) => { const m = 1 + osc(HAZE_MOTION[k], t); skyU.uHaze.value[k].set(hz.color[0] * m / 255, hz.color[1] * m / 255, hz.color[2] * m / 255, hz.eps); });
  SKY_INIT.blobs.forEach((g, i) => {
    const m = SKY_MOTION[i];
    const az = g.az + m.w * t + osc(m.az, t), el = clampN(g.el + osc(m.el, t), 0, 1.45);
    skyU.uBlobPos.value[i].set(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));
    const sigma = g.sigma * (1 + osc(m.size, t)), strength = clampN(1 + osc(m.str, t), 0.2, 1.8);
    skyU.uBlobK.value[i] = 1 / (sigma * sigma);
    skyU.uBlobCol.value[i].set(...g.color.map((c, k) => (c + Math.sign(c || 1) * osc(m.hue[k], t)) * strength / 255));
  });
}
let skyT = SKY_FITTED ? 0 : (skyQ.has('t') ? +skyQ.get('t') || 0 : 60 + Math.random() * 540);
applySky(skyT);

const sky = new THREE.Mesh(
  new THREE.SphereGeometry(7000, 48, 24),
  new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    defines: { SKY_N, HAZE_N },
    uniforms: Object.assign({ uF: { value: F_REF }, uGround: { value: rgb(GROUND) } }, skyU),
    vertexShader: `varying vec3 vDir; void main(){ vDir = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      uniform float uF; uniform vec3 uGround, uBase; uniform vec4 uHaze[HAZE_N];
      uniform vec3 uBlobPos[SKY_N], uBlobCol[SKY_N]; uniform float uBlobK[SKY_N];
      varying vec3 vDir;
      vec3 srgb2lin(vec3 c){ return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
      void main(){
        vec3 d = normalize(vDir);
        float h = uF * d.y / max(length(d.xz), 1e-4);                 // below the horizon is ground
        if (h < 0.0) { gl_FragColor = vec4(uGround, 1.0); return; }
        vec3 col = uBase;
        for (int k = 0; k < HAZE_N; k++) col += uHaze[k].rgb * exp(-d.y / uHaze[k].w);
        for (int i = 0; i < SKY_N; i++) col += uBlobCol[i] * exp((dot(d, uBlobPos[i]) - 1.0) * uBlobK[i]);
        gl_FragColor = vec4(srgb2lin(clamp(col, 0.0, 1.0)), 1.0);
      }`,
  })
);
sky.renderOrder = -10; sky.frustumCulled = false;
scene.add(sky);'''
s = s[:i] + sky + s[j:]

# 3. a Sky slider: how fast the sky evolves
rep('  <label for="int">', '  <label for="sky"><span class="squeeze" id="o_sky" data-name="Sky">Sky</span></label><div class="line"><canvas aria-hidden="true"></canvas><input id="sky" type="range" min="0" max="4" step="0.05" value="1"></div>\n  <label for="int">')
rep("bind('int','interval',", "bind('sky','sky', v => v === 0 ? 'frozen' : v.toFixed(2) + '×');\nbind('int','interval',")
rep("const TAU = { speed: 1.4,", "const TAU = { sky: 0.8, speed: 1.4,")
rep("  smoothControls(dt);\n", "  smoothControls(dt);\n  skyT += dt * V.sky; applySky(skyT);                                  // the sky evolves\n")
rep("window.__S = S; window.__V = V;", "window.__skyT = t => { skyT = t; applySky(t); }; window.__sky = () => ({ seed: SKY_SEED, t: +skyT.toFixed(1), link: `${location.origin}${location.pathname}?seed=${SKY_SEED}&t=${skyT.toFixed(0)}` }); window.__step = (dt = 1 / 60) => { update(dt); renderFrame(); }; window.__S = S; window.__V = V;")
open('index.html', 'w').write(s)
print('applied; globs:', len(fit["blobs"]), 'haze bands:', len(fit["haze"]), 'fit RMS', fit["rms_bytes"], 'frame RMS', fit["frame_rms_bytes"])
