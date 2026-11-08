# Grainy Nightmare

Real-time 3D recreation of a photograph of a wind farm at dusk: sampled colours, film grain, swaying grass and flashing red beacons.

**Live:** [mpts.ie/games/grainy](https://mpts.ie/games/grainy/)

| Source photograph | Windmills |
|---|---|
| ![Source photograph](docs/00-reference.webp) | ![Windmills](docs/01-windmills.jpg) |

| Pylons 1 | Pylons 2 |
|---|---|
| ![Pylons 1](docs/02-pylons-1.jpg) | ![Pylons 2](docs/03-pylons-2.jpg) |

| Blank | Controls |
|---|---|
| ![Blank](docs/04-blank.jpg) | ![Controls](docs/05-hud.jpg) |

| Walking | Under a pylon |
|---|---|
| ![Walking](docs/06-walk-field.jpg) | ![Under a pylon](docs/07-walk-under-pylon.jpg) |

| Windmill close-up | Phone |
|---|---|
| ![Windmill close-up](docs/09-windmill-closeup.jpg) | ![Phone](docs/15-phone-windmills.jpg) |

## Controls

| Input | Action |
|---|---|
| Sliders | Wind, wind direction, gusts, grass, sky evolution, blink rate, bloom, grain |
| `E` | Walk the scene (`E` again to return) |
| `WASD`, `Shift`, drag | Move, run, look around |

On a phone, tap **E · Walk** and use the left thumb joystick.

## Running it

```bash
python3 -m http.server   # then open http://localhost:8000
```

## License

The code is [MIT](LICENSE).
