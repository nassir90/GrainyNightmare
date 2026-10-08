// Stark shots: 6 skies × 13 shots, 5 s each, 1080 × 1920.
//   node ~/projects/TapaTab/tapatab.mjs promo/takes.mjs
//   EVOLUTION=15 BLINK=6 node ~/projects/TapaTab/tapatab.mjs promo/takes.mjs --jobs 3   (sky speed, seconds between flashes)
// The page's debug hooks (__go, __walk, __setWalk, __cam, __S) are on window; setup reads the shot from the query string.
const SKIES = { '1-dusk': 'sky=fitted', '2-blue': 'seed=11&t=300', '3-violet': 'seed=33&t=300', '4-plum': 'seed=44&t=300',
                '5-teal': 'seed=66&t=300', '6-green': 'seed=3065687849&t=158' };
const EVOLUTION = process.env.EVOLUTION || 1;   // how fast the sky evolves: 1 is the game's default
const BLINK = process.env.BLINK || 6;          // the Blink slider: seconds between each beacon's flashes (the game's default is 28)
const SHOTS = ['windmills', 'pylons-1', 'pylons-2', 'under-pylon', 'windmill-foot', 'beneath-wires',
               'hub-height', 'pylon-crown', 'up-the-tower', 'along-the-wires', 'beacon-field', 'crane-rise', 'pylon-orbit'];

const takes = {};
for (const [sky, q] of Object.entries(SKIES))
  SHOTS.forEach((name, i) => { takes[`${sky}_${String(i + 1).padStart(2, '0')}-${name}`] = { seconds: 5, page: `index.html?${q}&evolution=${EVOLUTION}&blink=${BLINK}&shot=${i}`, script: [] }; });

export default {
  app: '..',
  size: [540, 960], dpr: 2,
  prerun: 10,                                   // let the scene fade in and rotors spin up before frame 0
  ready: () => typeof window.__go === 'function',
  // recording only: let the walk camera leave eye height (window.__eyeH, metres above the ground) for the high and low angles
  inject: { replace: 'ty = gy + EYE + bob', code: 'ty = gy + (window.__eyeH ?? EYE) + bob' },
  css: '#controls, #scenes, #exitbtn, #joy { display: none !important }',
  setup() {
    const i = +new URLSearchParams(location.search).get('shot');
    const WALK = { 3: [1, 36, -148, 0.08, 0.62], 4: [0, 44, -255, -0.099, 0.6], 5: [2, -60, -205, 0.315, 0.42] };
    const W = window.__walk, q = new URLSearchParams(location.search), speed = +q.get('evolution') || 1;
    // rewind the sky by what the 10 s prerun will add at this speed, so frame 0 shows the same sky at every speed
    window.__skyT((q.get('sky') === 'fitted' ? 0 : +q.get('t')) + 10 - 10 * speed);
    window.__S.hold = false; window.__S.interval = +q.get('blink');   // short enough that the clips catch flashes
    if (i < 3) { window.__go(i); return; }
    if (i < 6) {
      const [sc, x, z, yaw, pitch] = WALK[i];
      window.__go(sc); window.__setWalk(true); W.w = 1; W.pos.set(x, 0, z); W.vel.set(0, 0); W.yaw = yaw; W.pitch = pitch; window.__cam.ready = false;
      return;
    }
    // free camera: [scene, camera [x, height, z], looking at [x, y, z]]
    const AIM = { 6: [0, [110, 45, -250], [49, 80, -310]],   7: [1, [46, 38, -150], [-14, 45, -345]],  8: [0, [53, 1.7, -310], [49, 200, -312]],
                  9: [2, [-470, 30, -200], [600, 38, -320]], 10: [0, [0, 140, -120], [-40, 0, -700]],  11: [0, [140, 3, -260], [49, 80, -310]],
                  12: [1, [93, 22, -145], [38, 30, -170]] };
    window.__aim = (P, T) => {
      const dx = T[0] - P[0], dz = T[2] - P[2];
      window.__eyeH = P[1]; W.pos.set(P[0], 0, P[2]); W.vel.set(0, 0);
      W.yaw = Math.atan2(-dx, -dz); W.pitch = Math.atan2(T[1] - P[1], Math.hypot(dx, dz));
    };
    const [sc, P, T] = AIM[i];
    window.__go(sc); window.__setWalk(true); W.w = 1; window.__aim(P, T); window.__cam.ready = false;
  },
  // moving shots: the crane rises from 3 m to hub height; the orbit swings 35° round the pylon (the camera's spring smooths both)
  each(t) {
    const i = +new URLSearchParams(location.search).get('shot'), u = Math.min(1, Math.max(0, t / 5)), ease = u * u * (3 - 2 * u);
    if (i === 11) window.__aim([140, 3 + 82 * ease, -260], [49, 80, -310]);
    if (i === 12) { const a = 0.43 + 0.6 * u; window.__aim([38 + 60 * Math.cos(a), 22, -170 + 60 * Math.sin(a)], [38, 30, -170]); }
  },
  takes,
};
