import os
import subprocess
import requests

def download_video(url, output_folder):
    """
    Descarga un vídeo de YouTube y lo guarda en la carpeta especificada.
    """
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        command = ["yt-dlp", "-f", "best", "--no-playlist", "-o", os.path.join(output_folder, "%(title)s.%(ext)s"), url]
        subprocess.run(command, check=True)
        print(f"\nVídeo descargado exitosamente en {output_folder}.")
    except subprocess.CalledProcessError as e:
        print(f"\nError al descargar el vídeo: {e}")
    except FileNotFoundError:
        print("\nyt-dlp no encontrado. Asegúrate de que está instalado y en tu PATH.")
        print("Puedes instalarlo con 'pip install yt-dlp' o consultando la documentación oficial.")

def convert_to_mp3(video_path, output_folder):
    """
    Convierte un archivo de vídeo a formato MP3 y lo guarda en la carpeta especificada.
    """
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        base_name = os.path.splitext(os.path.basename(video_path))[0]
        mp3_path = os.path.join(output_folder, f"{base_name}.mp3")

        command = ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", mp3_path]
        subprocess.run(command, check=True)
        print(f"\nArchivo convertido exitosamente a MP3: {mp3_path}")
    except subprocess.CalledProcessError as e:
        print(f"\nError al convertir el archivo: {e}")
    except FileNotFoundError:
        print("\nffmpeg no encontrado. Asegúrate de que está instalado y en tu PATH.")
        print("Puedes instalarlo consultando la documentación oficial.")

def transcribe_audio(mp3_path):
    """
    Transcribe un archivo MP3 usando la API de OpenAI.
    """
    try:
        api_url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": "Bearer YOUR_API_KEY"
        }
        files = {
            "file": open(mp3_path, "rb")
        }
        data = {
            "model": "whisper-1"
        }

        response = requests.post(api_url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            transcription = response.json().get("text", "")
            print(f"\nTranscripción: {transcription}")
        else:
            print(f"\nError en la transcripción: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"\nError al transcribir el archivo: {e}")

if __name__ == "__main__":
    video_url = input("Introduce la URL del vídeo de YouTube: ")
    output_folder = os.path.join(os.path.expanduser("~"), "Descargas", "video_to_mp3")

    if video_url:
        download_video(video_url, output_folder)

        # Buscar el archivo descargado
        for file in os.listdir(output_folder):
            if file.endswith(('.mp4', '.mkv', '.webm')):
                video_path = os.path.join(output_folder, file)
                convert_to_mp3(video_path, output_folder)

                # Transcribir el archivo MP3
                mp3_path = os.path.join(output_folder, f"{os.path.splitext(file)[0]}.mp3")
                transcribe_audio(mp3_path)
    else:
        print("No se proporcionó ninguna URL.")