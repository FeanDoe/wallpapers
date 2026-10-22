# wallpapers.tugurio.cl

Fuente "Generic JSON" para [RandomWallpaperGnome3](https://github.com/ifl0w/RandomWallpaperGnome3/wiki/Generic-JSON-Source).

## Agregar wallpapers
Copia imágenes a `wallpapers/`, corre `python3 exif.py` y haz push a `main`.
`exif.py` deja en los JPEG solo fecha/hora, zona horaria y orientación (borra GPS,
modelo de cámara, número de serie, XMP, miniaturas, etc.). El build falla si algún JPEG
no está limpio. El workflow genera:
- `https://wallpapers.tugurio.cl/<imagen>`
- `https://wallpapers.tugurio.cl/wallpapers.json` → `[{"url": "https://wallpapers.tugurio.cl/<imagen>"}, ...]`

Probar localmente: `python3 build.py && python3 -m http.server -d _site`

## Configuración en RandomWallpaperGnome3
- Request URL: `https://wallpapers.tugurio.cl/wallpapers.json`
- Image JSON Path: `$[@random].url`

## DNS
Registro `CNAME wallpapers` → `<tu-usuario>.github.io`, y en el repo:
Settings → Pages → Source: **GitHub Actions**, custom domain `wallpapers.tugurio.cl`, Enforce HTTPS.
