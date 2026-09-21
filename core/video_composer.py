import subprocess
import os
import re
import math
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core.character_registry import get_character, get_matchup, CHARACTERS
from core.tts_engine import ensure_ffmpeg

def draw_text_with_glow(draw, pos, text, font, fill_color, stroke_color, glow_color=None, stroke_w=8, glow_w=16):
    x, y = pos
    if glow_color and glow_w > 0:
        for dx in range(-glow_w, glow_w + 1, 4):
            for dy in range(-glow_w, glow_w + 1, 4):
                if dx * dx + dy * dy <= glow_w * glow_w:
                    draw.text((x + dx, y + dy), text, font=font, fill=glow_color)
    for dx in range(-stroke_w, stroke_w + 1):
        for dy in range(-stroke_w, stroke_w + 1):
            if dx * dx + dy * dy <= stroke_w * stroke_w:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
    draw.text((x, y), text, font=font, fill=fill_color)

def fit_character(im, max_w, max_h):
    bbox = im.getbbox()
    im_trim = im.crop(bbox) if bbox else im
    asp = im_trim.width / im_trim.height
    h_fit = max_h
    w_fit = int(h_fit * asp)
    if w_fit > max_w:
        w_fit = max_w
        h_fit = int(w_fit / asp)
    return im_trim.resize((w_fit, h_fit), Image.Resampling.LANCZOS)

def smart_tokenize_jp(text):
    """
    Split text into granular tokens while keeping bracketed keywords intact.
    Attaches punctuation to the preceding token.
    """
    raw = re.split(r'(「[^」]+」|[！!？?。、…]+)', text)
    tokens = []
    for r in raw:
        if not r:
            continue
        if re.match(r'^[！!？?。、…]+$', r):
            if tokens and not (tokens[-1].startswith('「') and tokens[-1].endswith('」')):
                tokens[-1] += r
            else:
                tokens.append(r)
        else:
            if len(r) > 14:
                sub = re.split(r'(から|けど|ので|のに|たら|なら)', r)
                buf = ''
                for s in sub:
                    buf += s
                    if s in ['から', 'けど', 'ので', 'のに', 'たら', 'なら'] or len(buf) >= 10:
                        tokens.append(buf)
                        buf = ''
                if buf:
                    tokens.append(buf)
            else:
                tokens.append(r)
    return [t for t in tokens if t]


def fit_font_to_width(font_path, text, max_w, start_size):
    size = start_size
    while size > 8:
        font = ImageFont.truetype(font_path, size)
        if font.getlength(text) <= max_w:
            return font
        size -= 2
    return ImageFont.truetype(font_path, 8)


def wrap_subtitle(text, font, max_w):
    pieces = []
    for token in smart_tokenize_jp(text):
        if font.getlength(token) <= max_w:
            pieces.append(token)
            continue
        piece = ""
        for char in token:
            if piece and font.getlength(piece + char) > max_w:
                pieces.append(piece)
                piece = ""
            piece += char
        if piece:
            pieces.append(piece)

    lines = []
    current = ""
    for piece in pieces:
        if current and font.getlength(current + piece) > max_w:
            lines.append(current)
            current = ""
        current += piece
    if current:
        lines.append(current)
    return lines

def layout_subtitles(text, font_path, max_w=900, target_fs=64, min_fs=42):
    """
    Auto-determine font size and multi-line breakdown for Japanese subtitles.
    Guarantees every line fits strictly within max_w pixels.
    """
    if '\n' in text:
        raw_lines = [l.strip() for l in text.split('\n') if l.strip()]
        for cur_fs in range(target_fs, 27, -2):
            f = ImageFont.truetype(font_path, cur_fs)
            lines = [wrapped for raw in raw_lines for wrapped in wrap_subtitle(raw, f, max_w)]
            if len(lines) <= 3 or cur_fs == 28:
                return [([p for p in re.split(r'(「[^」]+」)', line) if p], f) for line in lines], f, cur_fs

    tokens = smart_tokenize_jp(text)

    # 1 Line check (only if text is short and fits easily)
    for fs in range(target_fs, min_fs - 1, -2):
        f = ImageFont.truetype(font_path, fs)
        bb = f.getbbox(text)
        if len(text) <= 13 and (bb[2] - bb[0]) <= max_w:
            tks = [p for p in re.split(r'(「[^」]+」)', text) if p]
            return [(tks, f)], f, fs

    # 2 Lines check
    for fs in range(target_fs - 4, min_fs - 1, -2):
        f = ImageFont.truetype(font_path, fs)
        best_split = None
        best_diff = float('inf')
        for i in range(1, len(tokens)):
            l1 = ''.join(tokens[:i])
            l2 = ''.join(tokens[i:])
            w1 = f.getbbox(l1)[2] - f.getbbox(l1)[0]
            w2 = f.getbbox(l2)[2] - f.getbbox(l2)[0]
            if w1 <= max_w and w2 <= max_w:
                diff = abs(w1 - w2)
                if diff < best_diff:
                    best_diff = diff
                    best_split = i
        if best_split is not None:
            l1_tks = [p for p in re.split(r'(「[^」]+」)', ''.join(tokens[:best_split])) if p]
            l2_tks = [p for p in re.split(r'(「[^」]+」)', ''.join(tokens[best_split:])) if p]
            return [(l1_tks, f), (l2_tks, f)], f, fs

    # Wrap long tokens by character when a natural dialogue break will not fit.
    for cur_fs in range(46, 27, -2):
        f = ImageFont.truetype(font_path, cur_fs)
        lines = wrap_subtitle(text, f, max_w)
        if len(lines) <= 3 or cur_fs == 28:
            return [([p for p in re.split(r'(「[^」]+」)', line) if p], f) for line in lines], f, cur_fs

class VideoComposer:
    def __init__(self, assets_dir="assets"):
        self.assets_dir = assets_dir
        self.width = 1080
        self.height = 1920
        self.fps = 30
        
        # Load fonts
        self.font_dela_big = ImageFont.truetype(f"{assets_dir}/fonts/font_dela.ttf", 98)
        self.font_dela_sub = ImageFont.truetype(f"{assets_dir}/fonts/font_dela.ttf", 60)
        self.font_sub_path = f"{assets_dir}/fonts/font_zenmaru.ttf"
        self.font_moral_head = ImageFont.truetype(f"{assets_dir}/fonts/font_dela.ttf", 76)
        self.font_moral_body = ImageFont.truetype(f"{assets_dir}/fonts/font_zenmaru.ttf", 54)
        
        self.sprites_cache = {}
        
        # Preload Mascot Cat
        mascot_path = f"{assets_dir}/characters/mascot_judge_cat.png"
        if os.path.exists(mascot_path):
            m_img = Image.open(mascot_path).convert("RGBA")
            self.mascot_cat = fit_character(m_img, max_w=230, max_h=250)
        else:
            self.mascot_cat = None
            
        # Preload Stamp
        stamp_path = f"{assets_dir}/props/stamp_guilty.png"
        if os.path.exists(stamp_path):
            self.stamp_img = Image.open(stamp_path).convert("RGBA")
        else:
            self.stamp_img = None

    def get_character_sprite(self, char_id, emotion="normal"):
        cache_key = f"{char_id}_{emotion}"
        if cache_key in self.sprites_cache:
            return self.sprites_cache[cache_key]
            
        char_conf = get_character(char_id)
        scale = char_conf.get("height_scale", 1.0)
        max_h = int(1300 * scale)
        max_w = 510
        
        char_path = f"{self.assets_dir}/characters"
        emo_file = os.path.join(char_path, f"{char_id}_{emotion}.png")
        if not os.path.exists(emo_file):
            emo_file = os.path.join(char_path, f"{char_id}_normal.png")
        if not os.path.exists(emo_file):
            emo_file = os.path.join(char_path, "boy_normal.png")
            
        img = Image.open(emo_file).convert("RGBA")
        
        # If judge, trim desk margins if needed
        if char_id == "judge":
            jw, jh = img.size
            img = img.crop((int(jw * 0.12), 0, int(jw * 0.88), jh))
            
        fitted = fit_character(img, max_w=max_w, max_h=max_h)
        self.sprites_cache[cache_key] = fitted
        return fitted

    def prepare_base_frame(self, bg_name, title_main, title_sub):
        bg_file = f"{self.assets_dir}/backgrounds/{bg_name}.jpg"
        if not os.path.exists(bg_file):
            bg_file = f"{self.assets_dir}/backgrounds/courtroom.jpg"
            if not os.path.exists(bg_file):
                bg_file = f"{self.assets_dir}/backgrounds/room_japan.jpg"
            
        bg = Image.open(bg_file).resize((self.width, self.height), Image.Resampling.LANCZOS).convert("RGBA")
        
        # Top gradient vignette for header text
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        for y in range(430):
            alpha = int(210 * (1.0 - y / 430.0))
            ov_draw.line([(0, y), (self.width, y)], fill=(0, 0, 0, alpha))
            
        base = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(base)
        
        # Main Header (e.g. サクッと笑える)
        bbox1 = self.font_dela_big.getbbox(title_main)
        t1_w = bbox1[2] - bbox1[0]
        t1_x = (self.width - t1_w) // 2
        draw_text_with_glow(draw, (t1_x, 75), title_main, self.font_dela_big,
                            fill_color=(255, 230, 50),
                            stroke_color=(0, 0, 0),
                            glow_color=(255, 255, 190, 180),
                            stroke_w=10, glow_w=20)
                            
        # Sub Header (e.g. 【裁判】スシロー迷惑テロの末路)
        subtitle_font = fit_font_to_width(f"{self.assets_dir}/fonts/font_dela.ttf", title_sub, self.width - 120, 60)
        bbox2 = subtitle_font.getbbox(title_sub)
        t2_w = bbox2[2] - bbox2[0]
        t2_x = (self.width - t2_w) // 2
        draw_text_with_glow(draw, (t2_x, 215), title_sub, subtitle_font,
                            fill_color=(255, 255, 255),
                            stroke_color=(0, 0, 0),
                            glow_color=None,
                            stroke_w=8, glow_w=0)
                            
        return base

    def pre_render_subtitles(self, timeline):
        """
        Pre-renders subtitles with smart wrapping and dynamic font scaling.
        Never clips outside the 1080px canvas (max_w=900px safe margins).
        """
        subs = {}
        for item in timeline:
            text = item["text"]
            speaker = item["speaker"]
            char_conf = get_character(speaker)
            normal_stroke = char_conf.get("sub_stroke", (20, 60, 160))
            
            sub_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(sub_layer)
            
            parsed_lines, font_used, fs = layout_subtitles(
                text, self.font_sub_path, max_w=900, target_fs=64, min_fs=42
            )
            
            num_lines = len(parsed_lines)
            line_h = int(fs * 1.25)
            total_block_h = num_lines * line_h
            start_y = 430 - (total_block_h // 2)
            
            for l_idx, (tokens, f) in enumerate(parsed_lines):
                y = start_y + l_idx * line_h
                token_widths = []
                for t_text in tokens:
                    bb = f.getbbox(t_text)
                    token_widths.append(bb[2] - bb[0])
                    
                total_w = sum(token_widths)
                curr_x = (self.width - total_w) // 2
                
                for t_text, t_w in zip(tokens, token_widths):
                    is_keyword = t_text.startswith("「") and t_text.endswith("」")
                    if is_keyword:
                        draw_text_with_glow(draw, (curr_x, y), t_text, f,
                                            fill_color=(255, 245, 80),
                                            stroke_color=(0, 180, 240),
                                            glow_color=(0, 240, 255, 200),
                                            stroke_w=10, glow_w=18)
                    else:
                        draw_text_with_glow(draw, (curr_x, y), t_text, f,
                                            fill_color=(255, 255, 255),
                                            stroke_color=normal_stroke,
                                            glow_color=(0, 0, 0, 180),
                                            stroke_w=10, glow_w=16)
                    curr_x += t_w
                    
            subs[item["index"]] = sub_layer
        return subs

    def render_moral_ending_card(self, frame, moral_lesson, t_end):
        draw = ImageDraw.Draw(frame)
        panel_top = 700
        panel_bottom = 1450
        panel_overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        p_draw = ImageDraw.Draw(panel_overlay)
        p_draw.rounded_rectangle([60, panel_top, self.width - 60, panel_bottom],
                                 radius=35, fill=(15, 20, 30, 235),
                                 outline=(255, 215, 0, 240), width=6)
        frame.alpha_composite(panel_overlay)
        
        # Red Hanko Stamp 【有罪】 slamming down
        if self.stamp_img:
            scale = 1.0
            if t_end < 0.25:
                scale = 1.0 + (0.25 - t_end) * 2.0
            stamp_w = int(360 * scale)
            stamp_h = int(360 * scale)
            stamp_resized = self.stamp_img.resize((stamp_w, stamp_h), Image.Resampling.LANCZOS)
            sx = (self.width - stamp_w) // 2
            sy = panel_top + 40 - int((stamp_h - 360) / 2)
            frame.paste(stamp_resized, (sx, sy), stamp_resized)

        # Header: 【本日の教訓】
        head_text = "【本日の教訓】"
        bb_head = self.font_moral_head.getbbox(head_text)
        h_w = bb_head[2] - bb_head[0]
        hx = (self.width - h_w) // 2
        hy = panel_top + 420
        draw_text_with_glow(draw, (hx, hy), head_text, self.font_moral_head,
                            fill_color=(255, 230, 60),
                            stroke_color=(0, 0, 0),
                            glow_color=(255, 215, 0, 190),
                            stroke_w=8, glow_w=18)
                            
        # Moral Lesson text: safely wrapped within 820px
        words = moral_lesson
        lines = []
        max_c = 15
        for i in range(0, len(words), max_c):
            lines.append(words[i:i+max_c])
            
        ly = hy + 130
        for line in lines:
            bb_l = self.font_moral_body.getbbox(line)
            l_w = bb_l[2] - bb_l[0]
            lx = (self.width - l_w) // 2
            draw_text_with_glow(draw, (lx, ly), line, self.font_moral_body,
                                fill_color=(255, 255, 255),
                                stroke_color=(0, 0, 0),
                                glow_color=None,
                                stroke_w=6, glow_w=0)
            ly += 85

    def render_video(self, timeline, total_duration, master_audio_path, output_mp4,
                     title_main="サクッと笑える", title_sub="【裁判】スシロー迷惑テロの末路",
                     bg_name="courtroom", moral_lesson=None,
                     speaker_a_id="judge", speaker_b_id="prisoner",
                     has_mascot=True, progress_callback=None):
        ensure_ffmpeg()

        base_frame = self.prepare_base_frame(bg_name, title_main, title_sub)
        sub_layers = self.pre_render_subtitles(timeline)
        
        total_frames = int(total_duration * self.fps)
        ending_start_t = max(0.0, total_duration - 2.5)
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self.width}x{self.height}",
            "-pix_fmt", "rgba",
            "-r", str(self.fps),
            "-i", "-",
            "-i", master_audio_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_mp4
        ]
        
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Base character positioning (bottom aligned)
        # Side-by-side positioning without overlap:
        # Speaker A at x = 35, Speaker B at x = width - sprite_b.width - 35
        # Bottom aligned at y = 1920 - height - 70
        bottom_margin = 70
        
        for f_idx in range(total_frames):
            t = f_idx / self.fps
            
            # Find active line in timeline
            active_item = None
            for item in timeline:
                if item["start"] <= t < item["end"]:
                    active_item = item
                    break
                    
            # Determine emotions & bobbing
            spk_a_emo = "normal"
            spk_b_emo = "normal"
            a_bob = 0
            b_bob = 0
            
            if active_item:
                speaker = active_item["speaker"]
                emo = active_item.get("emotion", "normal")
                # Fast comedic dialogue bobbing
                bob_val = int(math.sin(t * 16.0) * 12)
                
                if speaker == speaker_a_id:
                    spk_a_emo = emo
                    a_bob = bob_val
                    # Counterpart reacts
                    spk_b_emo = "sweat" if emo in ["angry", "normal"] else "normal"
                else:
                    spk_b_emo = emo
                    b_bob = bob_val
                    spk_a_emo = "angry" if emo in ["sweat", "shocked"] else "normal"

            # Prepare frame composite
            frame = base_frame.copy()
            
            # Draw Character A (Left)
            spr_a = self.get_character_sprite(speaker_a_id, spk_a_emo)
            pos_a_x = 35
            pos_a_y = self.height - spr_a.height - bottom_margin + a_bob
            frame.paste(spr_a, (pos_a_x, pos_a_y), spr_a)
            
            # Draw Character B (Right)
            spr_b = self.get_character_sprite(speaker_b_id, spk_b_emo)
            pos_b_x = self.width - spr_b.width - 35
            pos_b_y = self.height - spr_b.height - bottom_margin + b_bob
            frame.paste(spr_b, (pos_b_x, pos_b_y), spr_b)
            
            # Draw Mascot Cat (Top Right corner)
            if has_mascot and self.mascot_cat:
                cat_bob = int(math.sin(t * 8.0) * 8)
                cat_x = self.width - self.mascot_cat.width - 20
                cat_y = 35 + cat_bob
                frame.paste(self.mascot_cat, (cat_x, cat_y), self.mascot_cat)

            # Overlay Subtitle
            if active_item and t < ending_start_t:
                sub_img = sub_layers.get(active_item["index"])
                if sub_img:
                    frame.alpha_composite(sub_img)
                    
            # Ending Card (Final 2.5s)
            if t >= ending_start_t and moral_lesson:
                t_end = t - ending_start_t
                self.render_moral_ending_card(frame, moral_lesson, t_end)

            proc.stdin.write(frame.tobytes())
                
            if progress_callback and f_idx % 30 == 0:
                progress_callback(f_idx / total_frames)

        proc.stdin.close()
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg render failed (exit code {proc.returncode})")
        
        if progress_callback:
            progress_callback(1.0)
            
        return output_mp4
