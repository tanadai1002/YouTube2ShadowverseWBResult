import os
import cv2
import ffmpeg
import argparse
import numpy as np
from pytubefix import YouTube
from glob import glob
import shutil
import csv

# === 引数 ===
parser = argparse.ArgumentParser(description="Download and classify Shadowverse match results.")
parser.add_argument("--url", required=True, help="YouTube video URL")
args = parser.parse_args()
youtube_url = args.url

# === ディレクトリ構成 ===
download_dir = "downloads"
split_dir = os.path.join(download_dir, "splits")
screenshots_dir = os.path.join(download_dir, "screenshots")
result_dirs = {
    "win": os.path.join(screenshots_dir, "win"),
    "lose": os.path.join(screenshots_dir, "lose"),
    "non_result": os.path.join(screenshots_dir, "non_result")
}

# === 1. フォルダ初期化 ===
if os.path.exists(download_dir):
    shutil.rmtree(download_dir)
os.makedirs(split_dir, exist_ok=True)
for base in result_dirs.values():
    os.makedirs(base, exist_ok=True)
    os.makedirs(base + "_top", exist_ok=True)

# === 2. テンプレート読み込み（上部20%）===
def load_top_templates(template_folder):
    templates = []
    for fname in sorted(os.listdir(template_folder)):
        path = os.path.join(template_folder, fname)
        img = cv2.imread(path)
        if img is not None:
            h, w = img.shape[:2]
            templates.append(img)
    return templates

win_templates = load_top_templates("win_templates_v2")
lose_templates = load_top_templates("lose_templates_v2")

# === 3. スクリーンショット分類＋保存 ===
def classify_and_save_with_score(frame, chunk_idx, sec, win_templates, lose_templates, threshold=0.80):
    h, w = frame.shape[:2]
    cropped = frame[0:int(h * 0.2), :]  # 上部20%

    def max_score(templates):
        scores = []
        for template in templates:
            try:
                temp_resized = cv2.resize(template, (cropped.shape[1], template.shape[0]))
                result = cv2.matchTemplate(cropped, temp_resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                scores.append(max_val)
            except Exception:
                continue
        return max(scores) if scores else 0.0

    win_score = max_score(win_templates)
    lose_score = max_score(lose_templates)

    if win_score > threshold and win_score > lose_score:
        label = "win"
        score = win_score
    elif lose_score > threshold:
        label = "lose"
        score = lose_score
    else:
        label = "non_result"
        score = max(win_score, lose_score)

    score_str = f"{score:.3f}"
    filename = f"chunk{chunk_idx:03d}_t{sec:04d}_{score_str}.jpg"
    full_path = os.path.join(result_dirs[label], filename)
    cropped_path = os.path.join(result_dirs[label] + "_top", filename)

    cv2.imwrite(full_path, frame)
    cv2.imwrite(cropped_path, cropped)

    return label, score

# === 4. 動画ダウンロード ===
print(f"[*] Downloading 360p video from {youtube_url}")
yt = YouTube(youtube_url)
stream = yt.streams.filter(progressive=True, file_extension='mp4', res="360p").first()
if not stream:
    raise Exception("360p stream not available.")
low_quality_file = os.path.join(download_dir, "low_quality.mp4")
stream.download(output_path=download_dir, filename="low_quality.mp4")
print(f"[+] Downloaded to {low_quality_file}")

# === 5. 5分ごとに分割 ===
print("[*] Splitting video into 5-minute chunks...")
os.makedirs(split_dir, exist_ok=True)
split_pattern = os.path.join(split_dir, "chunk_%03d.mp4")
(
    ffmpeg
    .input(low_quality_file)
    .output(split_pattern, f='segment', segment_time=300, reset_timestamps=1, c='copy')
    .overwrite_output()
    .run()
)
split_files = sorted(glob(os.path.join(split_dir, "chunk_*.mp4")))
print(f"[+] Total chunks: {len(split_files)}")

# === 6. 3秒ごとにスクリーンショット + 判定 ===
print("[*] Capturing and classifying every 3 seconds...")
total_shots = 0
last_result_time = -9999  # 最後のリザルト時刻（秒）

skip_count = 0

for i, chunk_path in enumerate(split_files):
    cap = cv2.VideoCapture(chunk_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    print(f"[+] Processing chunk {i:03d} ({duration:.2f} sec)")

    for sec in range(0, int(duration), 3):
        # if sec - last_result_time < 2:
        #     continue
        if skip_count > 0:
            skip_count -= 1
            continue

        cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        ret, frame = cap.read()
        if not ret:
            continue

        label, score = classify_and_save_with_score(
            frame, i, sec, win_templates, lose_templates
        )

        if label in ("win", "lose"):
            skip_count = 20

        total_shots += 1

    cap.release()

# === 7. ダウンロード動画削除 ===
if os.path.exists(low_quality_file):
    os.remove(low_quality_file)

# === 8. 結果をCSVに追記（日時なし・動画URL付き） ===
csv_file = "result_summary.csv"
file_exists = os.path.isfile(csv_file)

win_count = len([f for f in os.listdir(result_dirs["win"]) if f.endswith(".jpg")])
lose_count = len([f for f in os.listdir(result_dirs["lose"]) if f.endswith(".jpg")])
match_count = win_count + lose_count

with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["動画URL", "試合数", "勝利数", "敗北数"])
    writer.writerow([youtube_url, match_count, win_count, lose_count])

print(f"[✓] Done. Total screenshots: {total_shots}")
print(f"[✓] CSV updated: {csv_file}")
