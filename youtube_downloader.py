
import subprocess

def download_youtube_video(url):
    """
    Descarga un vídeo de YouTube dada su URL.
    """
    try:
        # Usamos yt-dlp para la descarga. La opción -f best significa la mejor calidad.
        # La opción --no-playlist evita descargar listas de reproducción completas si se proporciona una URL de lista de reproducción.
        command = ["yt-dlp", "-f", "best", "--no-playlist", url]
        subprocess.run(command, check=True)
        print(f"\nVídeo de {url} descargado exitosamente.")
    except subprocess.CalledProcessError as e:
        print(f"\nError al descargar el vídeo: {e}")
    except FileNotFoundError:
        print("\nyt-dlp no encontrado. Asegúrate de que está instalado y en tu PATH.")
        print("Puedes instalarlo con 'pip install yt-dlp' o consultando la documentación oficial.")

if __name__ == "__main__":
    video_url = input("Por favor, introduce la URL del vídeo de YouTube a descargar: ")
    if video_url:
        download_youtube_video(video_url)
    else:
        print("No se proporcionó ninguna URL.")
