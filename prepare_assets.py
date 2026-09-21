import urllib.request
import shutil
import os
from PIL import Image

bg1_src = r"C:\Users\ASUS\.gemini\antigravity\brain\d1e481c9-01ea-4c71-bbad-e54bb5725b1e\anime_room_bg_1789745110258.jpg"
bg2_src = r"C:\Users\ASUS\.gemini\antigravity\brain\d1e481c9-01ea-4c71-bbad-e54bb5725b1e\classroom_bg_1789745176597.jpg"

bg_dir = r"irasutoya_shorts_generator\assets\backgrounds"
os.makedirs(bg_dir, exist_ok=True)

if os.path.exists(bg1_src):
    shutil.copy2(bg1_src, os.path.join(bg_dir, "room_japan.jpg"))
    print("Copied room_japan.jpg")
if os.path.exists(bg2_src):
    shutil.copy2(bg2_src, os.path.join(bg_dir, "classroom.jpg"))
    print("Copied classroom.jpg")

# Download Irasutoya characters
char_dir = r"irasutoya_shorts_generator\assets\characters"
os.makedirs(char_dir, exist_ok=True)

chars = {
    "boy_gakuran.png": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEiPni3oY7j3cxO9PbVfXRbUYCywaon3NczXBcrXV5VEyvalmwtYMmsbEX33DQsIsacIpFmu97uewZyLFhSU_b0XIWLepN7B9O6PW6vRF-8gdjIDPPJEVv18sg9bNR42XREZUSMvF9gvO9o/s800/seifuku1_gakuran.png",
    "girl_blazer.png": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgsFiF890ydvyTXHhXwaIgtpzkLRQYUr4ie1G77tmKjPst9oZMmWOmK6PUalzFtdb_v0g77eqBkbXlziivx0sgGuVOZdefnax2z5w5vD56KwSFSryz8o-pX2UTdjB2bKMV0s19vyS2mpEo/s800/seifuku4_blazer_girl.png"
}

headers = {'User-Agent': 'Mozilla/5.0'}
for fname, url in chars.items():
    dst = os.path.join(char_dir, fname)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp, open(dst, 'wb') as out:
            out.write(resp.read())
        print(f"Downloaded {fname} ({os.path.getsize(dst)} bytes)")
    except Exception as e:
        print(f"Error downloading {fname}: {e}")
