import os
import json
import time
import requests
import yt_dlp

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TIKTOK_USERS = [
    "yobp_", "abriil.michel", "claudiaarcelemaitre", "mish_mend", 
    "cloecarpino__", "pilita_castro", "lorenaqueiroz", "aurora_di_marco", "jendii_barbii"
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
            # Extraemos los últimos 10 videos para asegurar que no se nos escape ninguno si hubo actividad masiva
            with yt_dlp.YoutubeDL({'extract_flat': 'in_playlist', 'quiet': True, 'playlistend': 10}) as ydl:
                info = ydl.extract_info(profile_url, download=False)
                if 'entries' not in info or not info['entries']:
                    continue 
                
                entries = info['entries']

            # Si la cuenta no está en el historial, inicializamos con el más reciente sin spamear
            if username not in historial:
                latest_id = entries[0].get('id')
                historial[username] = latest_id
                print(f"Historial inicializado para @{username} (ID: {latest_id})")
                hubo_cambios = True
                continue

            last_id = historial[username]

            # Buscamos todos los videos que sean más nuevos que el último registrado
            nuevos_videos = []
            for entry in entries:
                v_id = entry.get('id')
                if v_id == last_id:
                    break  # Encontramos el límite de lo que ya se había enviado
                nuevos_videos.append(entry)

            if nuevos_videos:
                print(f"¡Se encontraron {len(nuevos_videos)} video(s) nuevo(s) para @{username}!")
                
                # Invertimos la lista para procesarlos del más antiguo al más nuevo
                nuevos_videos.reverse()

                for entry in nuevos_videos:
                    video_id = entry.get('id')
                    video_url = entry.get('url') or f"https://www.tiktok.com/@{username}/video/{video_id}"
                    title = entry.get('title', f'Nuevo video de @{username}')

                    print(f"Descargando video ID {video_id} de @{username}...")
                    
                    ydl_download_opts = {
                        'format': 'best[ext=mp4]/best',
                        'outtmpl': 'downloaded_video.mp4',
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
                        ydl.download([video_url])

                    send_telegram_video('downloaded_video.mp4', f"🚨 ¡Nuevo video de @{username}!\n\n{title}")
                    
                    # Pausa de 5 segundos vital entre cada envío múltiple para no saturar Telegram
                    time.sleep(5)

                # Actualizamos el historial con el ID del video más reciente procesado
                historial[username] = entries[0].get('id')
                hubo_cambios = True
            else:
                print(f"No hay videos nuevos para @{username}.")

        except Exception as e:
            print(f"Error al procesar a {username}: {e}")

    # Guardamos los cambios en el archivo JSON local y actualizamos GitHub
    if hubo_cambios:
        guardar_historial(historial)
        print("Actualizando archivo de historial en GitHub...")
        os.system("git config --global user.name 'GitHub Actions Bot'")
        os.system("git config --global user.email 'actions@github.com'")
        os.system("git add historial_videos.json")
        os.system("git commit -m 'Actualizar historial multi-video de TikTok [skip ci]'")
        os.system("git push")

if __name__ == "__main__":
    check_accounts()
