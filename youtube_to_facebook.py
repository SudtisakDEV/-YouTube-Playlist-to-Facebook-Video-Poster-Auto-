import yt_dlp
import os
import subprocess
import json
import math

# === CONFIG ===
PLAYLIST_URL = 'https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID'
FFMPEG_PATH = 'ffmpeg/bin/ffmpeg.exe'
FFPROBE_PATH = 'ffmpeg/bin/ffprobe.exe'
DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === HELPER ===
def sanitize(name):
    return name.replace('/', '_').replace('\\', '_').replace(':', '_')

def get_duration_sec(file_path):
    result = subprocess.run([
        FFPROBE_PATH, '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout)

def split_video(file_path, part_duration_sec, base_title):
    duration = get_duration_sec(file_path)
    part_count = math.ceil(duration / part_duration_sec)
    part_files = []

    for i in range(part_count):
        start = int(i * part_duration_sec)
        output_file = os.path.join(DOWNLOAD_DIR, f"{base_title}_part{i+1}.mp4")
        cmd = [
            FFMPEG_PATH, '-y', '-i', file_path,
            '-ss', str(start),
        ]
        if i < part_count - 1:
            cmd += ['-t', str(int(part_duration_sec))]
        cmd += ['-c', 'copy', output_file]
        subprocess.run(cmd)
        part_files.append((output_file, f"{base_title} (Part {i+1}/{part_count})"))
    return part_files

# === STEP 1: DOWNLOAD PLAYLIST ===
video_list = []
ydl_opts = {
    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'write_thumbnail': True,
    'writethumbnail': True,
    'embed_thumbnail': True,
    'postprocessors': [
        {'key': 'EmbedThumbnail'},
        {'key': 'FFmpegMetadata'}
    ],
    'noplaylist': False
}

print("📥 เริ่มโหลด Playlist...")
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    playlist = ydl.extract_info(PLAYLIST_URL, download=True)

    for entry in playlist['entries']:
        raw_title = entry['title']
        safe_title = sanitize(raw_title)
        filename = f"{safe_title}.mp4"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        duration = get_duration_sec(filepath)
        print(f"⏱ {safe_title} → {int(duration//60)} นาที")

        if duration >= 3600:  # > 1 ชั่วโมง
            print("✂️ แบ่งวิดีโอเป็น part ละ 30 นาที")
            parts = split_video(filepath, 1800, safe_title)
            for fpath, part_title in parts:
                video_list.append({
                    "file": os.path.basename(fpath),
                    "title": part_title,
                    "description": f"🎬 รับชม: {part_title}\n#ดูฟรี #อนิเมะ",
                    "tags": "อนิเมะ,anime,youtube,playlist",
                    "content_category": "entertainment"
                })
        elif duration <= 1800:  # ≤ 30 นาที
            video_list.append({
                "file": filename,
                "title": raw_title,
                "description": f"🎬 รับชม: {raw_title}\n#ดูฟรี #อนิเมะ",
                "tags": "อนิเมะ,anime,youtube,playlist",
                "content_category": "entertainment"
            })
        else:
            # กลาง ๆ (31–59 นาที) โพสต์ทั้งคลิป
            video_list.append({
                "file": filename,
                "title": raw_title,
                "description": f"🎬 รับชม: {raw_title}\n#ดูฟรี #อนิเมะ",
                "tags": "อนิเมะ,anime,youtube,playlist",
                "content_category": "entertainment"
            })

# === STEP 2: SAVE video_list.json ===
with open("video_list.json", "w", encoding="utf-8") as f:
    json.dump(video_list, f, ensure_ascii=False, indent=2)

print(f"✅ สร้าง video_list.json แล้วทั้งหมด {len(video_list)} คลิป พร้อมยิงโพสต์!")
