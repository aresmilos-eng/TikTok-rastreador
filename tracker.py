import os
import requests
import yt_dlp

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ⚠️ REEMPLAZA esta variable con el usuario de TikTok que quieres rastrear (sin el @)
TIKTOK_USER = "yobp_"

HISTORY_FILE = "ultimo_video.txt"

def send_telegram_video(video_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    with open(video_path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"video": f})

def check_tiktok():
    profile_url = f"https://www.tiktok.com/@{TIKTOK_USER}"
    
    with yt_dlp.YoutubeDL({'extract_flat': 'in_playlist', 'quiet': True}) as ydl:
        info = ydl.extract_info(profile_url, download=False)
        if 'entries' not in info or not info['entries']:
            return
        
        latest = info['entries'][0]
        video_id = latest.get('id')
        video_url = latest.get('url') or f"https://www.tiktok.com/@{TIKTOK_USER}/video/{video_id}"
        title = latest.get('title', 'Nuevo video de TikTok')

    last_id = ""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            last_id = f.read().strip()

    if video_id != last_id:
        ydl_download_opts = {
            'outtmpl': 'downloaded_video.mp4',
            'format': 'best',
        }
        with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
            ydl.download([video_url])

        send_telegram_video('downloaded_video.mp4', f"🚨 ¡Nuevo video detectado!\n\n{title}")

        with open(HISTORY_FILE, "w") as f:
            f.write(video_id)

if __name__ == "__main__":
    check_tiktok()
