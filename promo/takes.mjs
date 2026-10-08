// Stark shots: 6 skies × 6 shots, 5 s each, 1080 × 1920.
//   node ~/projects/TapaTab/tapatab.mjs promo/takes.mjs
//   SKYSPEED=20 node ~/projects/TapaTab/tapatab.mjs promo/takes.mjs --jobs 3   (a faster-evolving sky)
// The page's debug hooks (__go, __walk, __setWalk, __cam, __S) are on window; setup reads the shot from the query string.
const SKIES = { '1-dusk': 'sky=fitted', '2-blue': 'seed=11&t=300', '3-violet': 'seed=33&t=300', '4-plum': 'seed=44&t=300',
                '5-teal': 'seed=66&t=300', '6-green': 'seed=3065687849&t=158' };
const SKYSPEED = process.env.SKYSPEED || 1;   // how fast the sky evolves: 1 is the game's default
const SHOTS = ['windmills', 'pylons-1', 'pylons-2', 'under-pylon', 'windmill-foot', 'beneath-wires'];

const takes = {};
for (const [sky, q] of Object.entries(SKIES))
  SHOTS.forEach((name, i) => { takes[`${sky}_${String(i + 1).padStart(2, '0')}-${name}`] = { seconds: 5, page: `index.html?${q}&skyspeed=${SKYSPEED}&shot=${i}`, script: [] }; });

export default {
  app: '..',
  size: [540, 960], dpr: 2,
  prerun: 10,                                   // let the scene fade in and rotors spin up before frame 0
  ready: () => typeof window.__go === 'function',
  css: '#controls, #scenes, #exitbtn, #joy { display: none !important }',
  setup() {
    const i = +new URLSearchParams(location.search).get('shot');
    const WALK = { 3: [1, 36, -148, 0.08, 0.62], 4: [0, 44, -255, -0.099, 0.6], 5: [2, -60, -205, 0.315, 0.42] };
    const W = window.__walk, q = new URLSearchParams(location.search), speed = +q.get('skyspeed') || 1;
    // rewind the sky by what the 10 s prerun will add at this speed, so frame 0 shows the same sky at every speed
    window.__skyT((q.get('sky') === 'fitted' ? 0 : +q.get('t')) + 10 - 10 * speed);
    window.__S.hold = false; window.__S.interval = 3;   // a 3 s blink so every clip catches flashes
    if (i < 3) { window.__go(i); return; }
    const [sc, x, z, yaw, pitch] = WALK[i];
    window.__go(sc); window.__setWalk(true); W.w = 1; W.pos.set(x, 0, z); W.vel.set(0, 0); W.yaw = yaw; W.pitch = pitch; window.__cam.ready = false;
  },
  takes,
};
