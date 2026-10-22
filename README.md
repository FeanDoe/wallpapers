# wallpapers.tugurio.cl

Fuente "Generic JSON" para [RandomWallpaperGnome3](https://github.com/ifl0w/RandomWallpaperGnome3/wiki/Generic-JSON-Source).

## Agregar wallpapers
Copia imágenes a `wallpapers/` y haz push a `main`. El workflow genera:
- `https://wallpapers.tugurio.cl/<imagen>`
- `https://wallpapers.tugurio.cl/wallpapers.json` → `[{"url": "https://wallpapers.tugurio.cl/<imagen>"}, ...]`

Probar localmente: `python3 build.py && python3 -m http.server -d _site`

## Configuración en RandomWallpaperGnome3
- Request URL: `https://wallpapers.tugurio.cl/wallpapers.json`
- Image JSON Path: `$[@random].url`

## DNS
Registro `CNAME wallpapers` → `<tu-usuario>.github.io`, y en el repo:
Settings → Pages → Source: **GitHub Actions**, custom domain `wallpapers.tugurio.cl`, Enforce HTTPS.
