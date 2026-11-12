import os
import requests
import yt_dlp

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TIKTOK_USERS = [
    "yobp_", "abriil.michel", "claudiaarcelemaitre", "mish_mend", 
    "cloecarpino__", "pilita_castro", "lorenaqueiroz", "aurora_di_marco"
]

def send_telegram_video(video_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    with open(video_path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"video": f})

def check_accounts():
    for username in TIKTOK_USERS:
        print(f"Revisando a: {username}")
        profile_url = f"https://www.tiktok.com/@{username}"
        history_file = f"ultimo_video_{username}.txt"
        
        try:
            with yt_dlp.YoutubeDL({'extract_flat': 'in_playlist', 'quiet': True}) as ydl:
                info = ydl.extract_info(profile_url, download=False)
                if 'entries' not in info or not info['entries']:
                    continue 
                
                latest = info['entries'][0]
                video_id = latest.get('id')
                video_url = latest.get('url') or f"https://www.tiktok.com/@{username}/video/{video_id}"
                title = latest.get('title', f'Nuevo video de @{username}')

            # Si el archivo de historial no existe, es la primera vez que se escanea esta cuenta.
            # Lo guardamos silenciosamente como referencia para NO spamear los videos viejos.
            if not os.path.exists(history_file):
                with open(history_file, "w") as f:
                    f.write(video_id)
                print(f"Historial inicializado para @{username} (ID: {video_id}). No se envía alerta de arranque.")
                continue

            # Leemos el último video registrado para esta cuenta específica
            with open(history_file, "r") as f:
                last_id = f.read().strip()

            # Si el ID actual es diferente al guardado, hay un video genuinamente nuevo
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

                # Actualizamos el historial con el nuevo ID
                with open(history_file, "w") as f:
                    f.write(video_id)
            else:
                print(f"No hay videos nuevos para @{username}.")

        except Exception as e:
            print(f"Error al procesar a {username}: {e}")

if __name__ == "__main__":
    check_accounts()
