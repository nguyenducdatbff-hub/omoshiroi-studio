from PIL import Image, ImageDraw

def add_sweat_drop(img, is_left=True):
    res = img.copy()
    draw = ImageDraw.Draw(res)
    # Draw a cute anime sweat drop 💧
    # Position: top corner of head
    cx = 120 if is_left else 320
    cy = 130
    
    # Draw water drop shape
    # Triangle top + circle bottom
    draw.polygon([(cx, cy - 28), (cx - 16, cy + 5), (cx + 16, cy + 5)], fill=(120, 210, 255, 230), outline=(50, 130, 200, 255))
    draw.ellipse([cx - 16, cy - 10, cx + 16, cy + 22], fill=(120, 210, 255, 230), outline=(50, 130, 200, 255))
    # highlight
    draw.ellipse([cx - 8, cy - 2, cx - 2, cy + 8], fill=(255, 255, 255, 240))
    return res

def add_shock_lines(img):
    res = img.copy()
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Dark blue/purple vertical shadow lines on top of face
    for x in range(140, 300, 14):
        draw.line([(x, 70), (x, 220)], fill=(70, 70, 140, 190), width=4)
        draw.line([(x + 5, 80), (x + 5, 200)], fill=(40, 40, 100, 150), width=2)
    
    # Combined with sweat drop
    res = Image.alpha_composite(res, overlay)
    return add_sweat_drop(res, is_left=False)

def add_blush(img):
    res = img.copy()
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Cute diagonal pink lines on cheeks
    # Left cheek
    for dx in range(0, 30, 8):
        draw.line([(140 + dx, 240), (155 + dx, 255)], fill=(255, 100, 120, 220), width=4)
    # Right cheek
    for dx in range(0, 30, 8):
        draw.line([(245 + dx, 240), (260 + dx, 255)], fill=(255, 100, 120, 220), width=4)
    return Image.alpha_composite(res, overlay)

def add_anger(img):
    res = img.copy()
    draw = ImageDraw.Draw(res)
    # Anime anger mark (red 4-branch cross 💢)
    cx, cy = 310, 100
    color = (230, 40, 40, 255)
    r = 16
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=0, end=90, fill=color, width=5)
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=90, end=180, fill=color, width=5)
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=180, end=270, fill=color, width=5)
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=270, end=360, fill=color, width=5)
    return res

char_dir = r"irasutoya_shorts_generator\assets\characters"

# Boy expressions
boy = Image.open(f"{char_dir}\\boy_gakuran.png").convert("RGBA")
boy.save(f"{char_dir}\\boy_normal.png")
add_sweat_drop(boy, is_left=False).save(f"{char_dir}\\boy_sweat.png")
add_shock_lines(boy).save(f"{char_dir}\\boy_shocked.png")
add_blush(boy).save(f"{char_dir}\\boy_blush.png")
add_anger(boy).save(f"{char_dir}\\boy_angry.png")

# Girl expressions
girl = Image.open(f"{char_dir}\\girl_blazer.png").convert("RGBA")
girl.save(f"{char_dir}\\girl_normal.png")
add_sweat_drop(girl, is_left=False).save(f"{char_dir}\\girl_sweat.png")
add_shock_lines(girl).save(f"{char_dir}\\girl_shocked.png")
add_blush(girl).save(f"{char_dir}\\girl_blush.png")
add_anger(girl).save(f"{char_dir}\\girl_angry.png")

print("Created all character emotion variants successfully!")
