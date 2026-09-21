import os
import sys
import uuid
import asyncio
import shutil
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional

# Add root directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Auto-add static FFmpeg to PATH if available
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

# Load .env if present
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from core.character_registry import DUO_MATCHUPS, CHARACTERS, get_matchup, get_character
from core.script_ai import get_presets, generate_script_from_prompt, GeminiGenerationError
from core.tts_engine import build_dialogue_timeline, mix_master_audio
from core.video_composer import VideoComposer
from core.caption_generator import generate_viral_caption, sanitize_folder_name, resolve_output_file


app = FastAPI(title="OMOSHIROI - Satirical Parable Shorts Studio")

OUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp_scratch")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

class DialogueLine(BaseModel):
    speaker: str
    text: str
    emotion: str = "normal"
    text_vi: Optional[str] = None

class RenderRequest(BaseModel):
    matchup: str = "courtroom"
    title_main: str = "サクッと笑える"
    title_sub: str = "【裁判】スシロー迷惑テロの末路"
    moral_lesson: Optional[str] = "ネットの10秒の目立ちたがり、代償は数千万円の借金地獄。"
    moral_lesson_vi: Optional[str] = None
    bg_name: str = "courtroom"
    voice_rate: str = "+6%"
    bgm_vol: float = 0.15
    dialogue: List[DialogueLine]

class AIGenerateRequest(BaseModel):
    topic: str
    matchup_id: str = "courtroom"
    api_key: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    template_path = os.path.join(BASE_DIR, "web", "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/presets")
async def api_presets():
    return get_presets()

@app.get("/api/matchups")
async def api_matchups():
    return {
        "matchups": DUO_MATCHUPS,
        "characters": CHARACTERS
    }

@app.get("/api/config_status")
async def api_config_status():
    return {
        "has_env_key": bool(os.environ.get("GEMINI_API_KEY"))
    }

@app.post("/api/generate_ai")
async def api_generate_ai(req: AIGenerateRequest):
    try:
        return await asyncio.to_thread(generate_script_from_prompt, req.topic, matchup_id=req.matchup_id, api_key=req.api_key)
    except GeminiGenerationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None

@app.post("/api/render_video")
async def api_render_video(req: RenderRequest):
    req_temp = None
    topic_dir = None
    try:
        dialogue_dicts = [d.model_dump() for d in req.dialogue]
        req_id = uuid.uuid4().hex
        new_req_temp = os.path.join(TEMP_DIR, f"run_{req_id}")
        os.makedirs(new_req_temp)
        req_temp = new_req_temp
        
        matchup_conf = get_matchup(req.matchup)
        
        # 1. Synthesize Audio
        rate = req.voice_rate if req.voice_rate else "+6%"
        timeline, total_duration = await build_dialogue_timeline(
            dialogue_dicts,
            temp_dir=req_temp,
            default_rate=rate
        )
        
        # 2. Mix Audio
        audio_dir = os.path.join(ASSETS_DIR, "audio")
        bgm_path = os.path.join(audio_dir, "bgm_comical.wav")
        sfx_pop = os.path.join(audio_dir, "sfx_pop.wav")
        sfx_punch = os.path.join(audio_dir, "sfx_punchline.wav")
        sfx_gavel = os.path.join(audio_dir, "sfx_gavel.wav") if matchup_conf.get("intro_sfx") else None
        sfx_stamp = os.path.join(audio_dir, "sfx_stamp.wav") if matchup_conf.get("has_stamp") else None
        master_wav = os.path.join(req_temp, "master_audio.wav")
        
        await asyncio.to_thread(mix_master_audio,
            timeline=timeline,
            total_duration=total_duration,
            bgm_path=bgm_path,
            sfx_pop_path=sfx_pop,
            sfx_punch_path=sfx_punch,
            out_wav_path=master_wav,
            bgm_vol=req.bgm_vol,
            intro_sfx_path=sfx_gavel,
            stamp_sfx_path=sfx_stamp
        )
        
        # 3. Create topic subfolder inside output/
        folder_name = f"{sanitize_folder_name(req.title_sub)}_{req_id[:8]}"
        new_topic_dir = os.path.join(OUT_DIR, folder_name)
        os.makedirs(new_topic_dir)
        topic_dir = new_topic_dir
        
        out_filename = f"{folder_name}.mp4"
        out_mp4 = os.path.join(topic_dir, out_filename)
        
        composer = VideoComposer(assets_dir=ASSETS_DIR)
        await asyncio.to_thread(composer.render_video,
            timeline=timeline,
            total_duration=total_duration,
            master_audio_path=master_wav,
            output_mp4=out_mp4,
            title_main=req.title_main,
            title_sub=req.title_sub,
            bg_name=req.bg_name if req.bg_name else matchup_conf.get("default_bg", "courtroom"),
            moral_lesson=req.moral_lesson,
            speaker_a_id=matchup_conf.get("speaker_a", "judge"),
            speaker_b_id=matchup_conf.get("speaker_b", "prisoner"),
            has_mascot=matchup_conf.get("has_mascot", True)
        )
        
        # 4. Generate sensational viral caption & Save caption.txt
        caption_content = generate_viral_caption(
            title_sub=req.title_sub,
            moral_lesson=req.moral_lesson,
            moral_lesson_vi=req.moral_lesson_vi,
            dialogue=dialogue_dicts
        )
        caption_path = os.path.join(topic_dir, "caption.txt")
        with open(caption_path, "w", encoding="utf-8") as f:
            f.write(caption_content)
            
        import urllib.parse
        encoded_folder = urllib.parse.quote(folder_name)
        encoded_file = urllib.parse.quote(out_filename)
        
        return {
            "success": True,
            "folder_name": folder_name,
            "folder_path": f"output/{folder_name}/",
            "video_url": f"/output/{encoded_folder}/{encoded_file}",
            "caption_url": f"/output/{encoded_folder}/caption.txt",
            "filename": out_filename,
            "caption": caption_content,
            "duration": total_duration
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        if topic_dir:
            shutil.rmtree(topic_dir, ignore_errors=True)
        return {"success": False, "error": str(e)}
    finally:
        if req_temp:
            shutil.rmtree(req_temp, ignore_errors=True)

@app.get("/output/{file_path:path}")
async def get_output_file(file_path: str):
    full_path = resolve_output_file(OUT_DIR, file_path)
    if full_path:
        media_type = "video/mp4" if full_path.suffix == ".mp4" else "text/plain; charset=utf-8"
        return FileResponse(full_path, media_type=media_type)
    raise HTTPException(status_code=404, detail="File not found")


if __name__ == "__main__":
    uvicorn.run("web.app:app", host="127.0.0.1", port=8001)
