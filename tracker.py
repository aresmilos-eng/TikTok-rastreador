import os
import json
import time
import glob
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

def limpiar_archivos_video(prefijo):
    for archivo in glob.glob(f"{prefijo}*"):
        try:
            os.remove(archivo)
        except Exception:
            pass

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
            with yt_dlp.YoutubeDL({'extract_flat': 'in_playlist', 'quiet': True, 'playlistend': 10}) as ydl:
                info = ydl.extract_info(profile_url, download=False)
                if 'entries' not in info or not info['entries']:
                    continue 
                
                entries = info['entries']

            if username not in historial:
                latest_id = entries[0].get('id')
                historial[username] = latest_id
                print(f"Historial inicializado para @{username} (ID: {latest_id})")
                hubo_cambios = True
                continue

            last_id = historial[username]

            nuevos_videos = []
            for entry in entries:
                v_id = entry.get('id')
                if v_id == last_id:
                    break
                nuevos_videos.append(entry)

            if nuevos_videos:
                print(f"¡Se encontraron {len(nuevos_videos)} video(s) nuevo(s) para @{username}!")
                nuevos_videos.reverse()

                for entry in nuevos_videos:
                    video_id = entry.get('id')
                    video_url = entry.get('url') or f"https://www.tiktok.com/@{username}/video/{video_id}"
                    title = entry.get('title', f'Nuevo video de @{username}')

                    base_name = f"video_{username}_{video_id}"
                    limpiar_archivos_video(base_name)

                    print(f"Descargando video ID {video_id} de @{username} en máxima calidad...")
                    
                    ydl_download_opts = {
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'outtmpl': f"{base_name}.mp4",
                        'merge_output_format': 'mp4',
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
                        ydl.download([video_url])

                    archivos_descargados = glob.glob(f"{base_name}*")
                    archivo_final = f"{base_name}.mp4" if os.path.exists(f"{base_name}.mp4") else (archivos_descargados[0] if archivos_descargados else None)

                    if archivo_final and os.path.exists(archivo_final):
                        send_telegram_video(archivo_final, f"🚨 ¡Nuevo video de @{username}!\n\n{title}")
                        limpiar_archivos_video(base_name)
                        time.sleep(5)
                    else:
                        print(f"No se pudo localizar el archivo descargado para {video_id} de @{username}.")

                historial[username] = entries[0].get('id')
                hubo_cambios = True
            else:
                print(f"No hay videos nuevos para @{username}.")

        except Exception as e:
            print(f"Error al procesar a {username}: {e}")

    if hubo_cambios:
        guardar_historial(historial)
        print("Actualizando archivo de historial en GitHub...")
        os.system("git config --global user.name 'GitHub Actions Bot'")
        os.system("git config --global user.email 'actions@github.com'")
        os.system("git add historial_videos.json")
        os.system("git commit -m 'Evitar cruce de archivos entre cuentas [skip ci]'")
        os.system("git push")

if __name__ == "__main__":
    check_accounts()
