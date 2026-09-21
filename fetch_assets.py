import urllib.request
import re
import os
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def fetch_image_from_page(page_url):
    req = urllib.request.Request(page_url, headers=headers)
    html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
    imgs = re.findall(r'(https://[0-9a-z\.]+\.blogspot\.com/[^\"\'\s>]+\.png)', html)
    # Convert any thumbnail URL /s72-c/ or /s400/ to full resolution /s800/
    res = []
    for img in imgs:
        full_res = re.sub(r'/s[0-9]+(-c)?/', '/s800/', img)
        res.append(full_res)
    return list(dict.fromkeys(res))

pages = {
    "boy_gakuran": "https://www.irasutoya.com/2013/05/blog-post_4176.html",
    "girl_seifuku": "https://www.irasutoya.com/2013/05/blog-post_8741.html",
    "boy_blazer": "https://www.irasutoya.com/2013/05/blog-post_7087.html",
    "girl_blazer": "https://www.irasutoya.com/2013/05/blog-post_8952.html",
    "students": "https://www.irasutoya.com/2014/10/blog-post_253.html"
}

results = {}
for name, url in pages.items():
    try:
        found = fetch_image_from_page(url)
        print(f"[{name}] -> {url} : {len(found)} pngs found")
        for f in found[:3]:
            print("   ", f)
        results[name] = found
    except Exception as e:
        print(f"Error fetching {name}: {e}")

out_path = os.path.join('irasutoya_shorts_generator', 'assets_found.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)
