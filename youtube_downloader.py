import os
import subprocess

def download_youtube_video(url):
    """
    Descarga un vídeo de YouTube dada su URL en la carpeta Descargas.
    """
    try:
        # Obtener la carpeta Descargas del usuario
        downloads_folder = os.path.join(os.path.expanduser("~"), "Descargas")
        if not os.path.exists(downloads_folder):
            os.makedirs(downloads_folder)

        # Usamos yt-dlp para la descarga. La opción -f best significa la mejor calidad.
        # La opción --no-playlist evita descargar listas de reproducción completas si se proporciona una URL de lista de reproducción.
        command = ["yt-dlp", "-f", "best", "--no-playlist", "-o", os.path.join(downloads_folder, "%(title)s.%(ext)s"), url]
        subprocess.run(command, check=True)
        print(f"\nVídeo de {url} descargado exitosamente en {downloads_folder}.")
    except subprocess.CalledProcessError as e:
        print(f"\nError al descargar el vídeo: {e}")
    except FileNotFoundError:
        print("\nyt-dlp no encontrado. Asegúrate de que está instalado y en tu PATH.")
        print("Puedes instalarlo con 'pip install yt-dlp' o consultando la documentación oficial.")

def download_youtube_playlist(urls, playlist_name):
    """
    Descarga una lista de reproducción de YouTube dada una lista de URLs y un nombre de playlist.
    """
    try:
        # Obtener la carpeta Descargas del usuario
        downloads_folder = os.path.join(os.path.expanduser("~"), "Descargas")
        playlist_folder = os.path.join(downloads_folder, playlist_name)
        if not os.path.exists(playlist_folder):
            os.makedirs(playlist_folder)

        for url in urls:
            print(f"Descargando: {url}")
            command = [
                "yt-dlp", "-f", "best", "--no-playlist",
                "-o", os.path.join(playlist_folder, "%(title)s.%(ext)s"), url
            ]
            subprocess.run(command, check=True)
        print(f"\nPlaylist '{playlist_name}' descargada exitosamente en {playlist_folder}.")
    except subprocess.CalledProcessError as e:
        print(f"\nError al descargar un vídeo: {e}")
    except FileNotFoundError:
        print("\nyt-dlp no encontrado. Asegúrate de que está instalado y en tu PATH.")
        print("Puedes instalarlo con 'pip install yt-dlp' o consultando la documentación oficial.")

if __name__ == "__main__":
    option = input("¿Qué deseas hacer? (1: Descargar un video, 2: Crear una playlist): ")
    if option == "1":
        video_url = input("Por favor, introduce la URL del vídeo de YouTube a descargar: ")
        if video_url:
            download_youtube_video(video_url)
        else:
            print("No se proporcionó ninguna URL.")
    elif option == "2":
        playlist_name = input("Introduce el nombre de la playlist: ")
        urls = input("Introduce las URLs de los videos separadas por comas: ").split(",")
        if playlist_name and urls:
            download_youtube_playlist(urls, playlist_name)
        else:
            print("No se proporcionaron datos suficientes para la playlist.")
    else:
        print("Opción no válida.")
