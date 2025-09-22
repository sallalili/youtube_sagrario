# multidescargas (Servidor MCP)

Servidor MCP en Python que expone herramientas para descargar vídeos con yt-dlp:

- download_video(url, format?)
- download_playlist(url)
- get_download_status(job_id)
- cancel_download(job_id)
- list_downloads()
- get_video_metadata(url)

## Requisitos

- Python 3.10+
- `pip install -r requirements.txt`
- ffmpeg en PATH (recomendado para combinar audio/vídeo)

## Uso local

```bash
python multidescargas_server.py
```

El servidor usa stdio y está listo para integrarse con un cliente MCP (por ejemplo, Claude Desktop).

## Configuración en Claude Desktop (MCP)

Edita tu archivo de configuración de Claude Desktop (ejemplo en Windows):

```
%APPDATA%/Claude/claude_desktop_config.json
```

Añade una entrada al bloque `mcpServers`:

```json
{
  "mcpServers": {
    "multidescargas": {
      "command": "python",
      "args": ["C:/sallalili/youtube_sagrario/multidescargas_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

Reinicia Claude Desktop. Deberías ver las tools del servidor `multidescargas` disponibles.

## Publicar en GitHub

1. Crea un repositorio nuevo en GitHub llamado `multidescargas`.
2. En la terminal:

```bash
git init
git add .
git commit -m "feat: servidor MCP multidescargas"
git branch -M main
git remote add origin https://github.com/<tu-usuario>/multidescargas.git
git push -u origin main
```

## Notas

- Si `yt-dlp` CLI no está en PATH, este servidor usa la librería Python `yt_dlp` directamente.
- Para descargas largas, usa `get_download_status` periódicamente; el campo `progress` es un porcentaje 0-100.
