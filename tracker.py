import os
import json
import requests
import yt_dlp

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TIKTOK_USERS = [
    "yobp_", "abriil.michel", "claudiaarcelemaitre", "mish_mend", 
    "cloecarpino__", "pilita_castro", "lorenaqueiroz", "aurora_di_marco", "jendii_Barbi"
]

HISTORY_FILE = "historial_videos.json"

def send_telegram_video(video_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    with open(video_path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"video": f})

def cargar_historial():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def guardar_historial(historial):
    with open(HISTORY_FILE, "w") as f:
        json.dump(historial, f, indent=4)

def check_accounts():
    historial = cargar_historial()
    hubo_cambios = False

    for username in TIKTOK_USERS:
        print(f"Revisando a: {username}")
        profile_url = f"https://www.tiktok.com/@{username}"
        
        try:
            with yt_dlp.YoutubeDL({'extract_flat': 'in_playlist', 'quiet': True}) as ydl:
                info = ydl.extract_info(profile_url, download=False)
                if 'entries' not in info or not info['entries']:
                    continue 
                
                latest = info['entries'][0]
                video_id = latest.get('id')
                video_url = latest.get('url') or f"https://www.tiktok.com/@{username}/video/{video_id}"
                title = latest.get('title', f'Nuevo video de @{username}')

            # Si la cuenta no está en el historial, la inicializamos sin spamear
            if username not in historial:
                historial[username] = video_id
                print(f"Historial inicializado para @{username} (ID: {video_id})")
                hubo_cambios = True
                continue

            # Comparamos con el último video registrado para esta cuenta
            last_id = historial[username]

            if video_id != last_id:
                print(f"¡Nuevo video encontrado para @{username}! Descargando...")
                ydl_download_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': 'downloaded_video.mp4',
                    'merge_output_format': 'mp4',
                }
                with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
                    ydl.download([video_url])

                send_telegram_video('downloaded_video.mp4', f"🚨 ¡Nuevo video de @{username}!\n\n{title}")

                # Actualizamos el registro con el nuevo ID
                historial[username] = video_id
                hubo_cambios = True
            else:
                print(f"No hay videos nuevos para @{username}.")

        except Exception as e:
            print(f"Error al procesar a {username}: {e}")

    # Guardamos los cambios en el archivo JSON local
    if hubo_cambios:
        guardar_historial(historial)
        print("Actualizando archivo de historial en GitHub...")
        os.system("git config --global user.name 'GitHub Actions Bot'")
        os.system("git config --global user.email 'actions@github.com'")
        os.system("git add historial_videos.json")
        os.system("git commit -m 'Actualizar historial de TikTok [skip ci]'")
        os.system("git push")

if __name__ == "__main__":
    check_accounts()
