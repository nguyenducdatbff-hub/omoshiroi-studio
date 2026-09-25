import os
import sys
import uuid
import asyncio
import math
import shutil
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from pydantic import BaseModel
from typing import List, Optional, Dict, Any

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
from core.script_evaluator import (
    evaluate_script,
    fingerprint_state,
    EvaluatorValidationError,
    EvaluatorConfigError,
    EvaluatorTimeoutError,
    EvaluatorUpstreamError,
)
from core.excel_importer import parse_script_file



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

class EvaluateScriptRequest(BaseModel):
    platform: str = "tiktok"
    content_profile: str = "irasutoya_short"
    target_audience: str = "Người xem Việt Nam thích anime và hài châm biếm"
    target_duration_seconds: int = 45
    matchup: str = "courtroom"
    title_main: str = "サクッと笑える"
    title_sub: str = "【裁判】スシロー迷惑テロの末路"
    moral_lesson: Optional[str] = "ネットの10秒の目立ちたがり、代償は数千万円の借金地獄。"
    dialogue: List[DialogueLine]

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
    evaluation: Optional[Dict[str, Any]] = None

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
        "has_env_key": bool(os.environ.get("GEMINI_API_KEY")),
        "has_gemini_key": bool(os.environ.get("GEMINI_API_KEY")),
        "has_typesafe_key": bool(os.environ.get("TYPESAFE_API_KEY")),
    }

@app.post("/api/evaluate_script")
async def api_evaluate_script(req: EvaluateScriptRequest):
    try:
        script_data = req.model_dump()
        result = await evaluate_script(script_data)
        return result
    except EvaluatorValidationError as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error": {"code": e.code, "message": e.message}}
        )
    except EvaluatorConfigError as e:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "error": {"code": e.code, "message": e.message}}
        )
    except EvaluatorTimeoutError as e:
        return JSONResponse(
            status_code=504,
            content={"status": "error", "error": {"code": e.code, "message": e.message}}
        )
    except EvaluatorUpstreamError as e:
        return JSONResponse(
            status_code=502,
            content={"status": "error", "error": {"code": e.code, "message": e.message}}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": {"code": "INTERNAL_ERROR", "message": "Lỗi nội bộ khi chấm điểm kịch bản."}}
        )

@app.post("/api/generate_ai")
async def api_generate_ai(req: AIGenerateRequest):
    try:
        return await asyncio.to_thread(generate_script_from_prompt, req.topic, matchup_id=req.matchup_id, api_key=req.api_key)
    except GeminiGenerationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None

@app.post("/api/import_excel")
async def api_import_excel(file: UploadFile = File(...), matchup: Optional[str] = "courtroom"):
    try:
        content = await file.read()
        matchup_info = None
        if matchup:
            try:
                matchup_info = get_matchup(matchup)
            except Exception:
                pass
        parsed = parse_script_file(content, file.filename, matchup_info)
        return {"success": True, "data": parsed}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Error processing Excel file upload")
        raise HTTPException(status_code=500, detail=f"Lỗi đọc file kịch bản: {str(e)}")


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
            
        # 5. Save evaluation.json if present (sanitized copy)
        evaluation_file_saved = False
        if req.evaluation and isinstance(req.evaluation, dict):
            import json
            submitted_eval = req.evaluation
            eval_fp = submitted_eval.get("input_fingerprint")
            evaluation_state = {
                "platform": submitted_eval.get("platform"),
                "content_profile": submitted_eval.get("content_profile"),
                "target_audience": submitted_eval.get("target_audience"),
                "target_duration_seconds": submitted_eval.get("target_duration_seconds"),
                "matchup": req.matchup,
                "title_main": req.title_main,
                "title_sub": req.title_sub,
                "moral_lesson": req.moral_lesson,
                "dialogue": dialogue_dicts,
            }
            current_fp = fingerprint_state(evaluation_state)
            score = submitted_eval.get("viral_score")
            valid_eval = (
                submitted_eval.get("status") == "ok"
                and isinstance(score, int) and not isinstance(score, bool) and 0 <= score <= 100
                and submitted_eval.get("classification") in {"recommended", "revise", "major_revision"}
                and isinstance(submitted_eval.get("dimensions"), dict)
                and isinstance(eval_fp, str) and eval_fp == current_fp
                and not submitted_eval.get("stale", False)
            )
            if valid_eval:
                known_dimensions = {"hook_strength", "curiosity_emotion", "retention_payoff", "share_comment"}
                dimensions = {}
                for key in known_dimensions:
                    value = submitted_eval["dimensions"].get(key)
                    required = ("score", "normalized", "confidence", "uncertain")
                    if not isinstance(value, dict) or any(name not in value for name in required):
                        dimensions = {}
                        break
                    try:
                        score_value = float(value["score"])
                        normalized_value = float(value["normalized"])
                        confidence_value = float(value["confidence"])
                    except (TypeError, ValueError):
                        dimensions = {}
                        break
                    probabilities = value.get("probabilities")
                    if probabilities is not None and (
                        not isinstance(probabilities, list) or len(probabilities) != 5
                        or any(not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities)
                    ):
                        dimensions = {}
                        break
                    if (
                        not math.isfinite(score_value) or not 0 <= score_value <= 4
                        or not math.isfinite(normalized_value) or not 0 <= normalized_value <= 1
                        or not math.isfinite(confidence_value) or not 0 <= confidence_value <= 1
                        or not isinstance(value["uncertain"], bool)
                    ):
                        dimensions = {}
                        break
                    dimensions[key] = {
                        "score": score_value,
                        "normalized": normalized_value,
                        "confidence": confidence_value,
                        "uncertain": value["uncertain"],
                        "probabilities": probabilities,
                    }
                if len(dimensions) == len(known_dimensions):
                    recommendations = submitted_eval.get("recommendations", [])
                    if not isinstance(recommendations, list):
                        recommendations = []
                    safe_recommendations = [
                        {
                            "code": str(item.get("code", ""))[:80],
                            "dimension": str(item.get("dimension", ""))[:80],
                            "message": str(item.get("message", ""))[:500],
                        }
                        for item in recommendations[:3] if isinstance(item, dict)
                    ]
                    warnings = submitted_eval.get("warnings", [])
                    if not isinstance(warnings, list):
                        warnings = []
                    safe_eval = {
                        "status": "ok",
                        "model": str(submitted_eval.get("model", ""))[:100],
                        "rubric_version": str(submitted_eval.get("rubric_version", ""))[:100],
                        "viral_score": score,
                        "classification": submitted_eval["classification"],
                        "overall_confidence": submitted_eval.get("overall_confidence"),
                        "dimensions": dimensions,
                        "weakest_dimension": submitted_eval.get("weakest_dimension") if submitted_eval.get("weakest_dimension") in known_dimensions else None,
                        "recommendations": safe_recommendations,
                        "warnings": [str(item)[:500] for item in warnings[:4]],
                        "evaluated_at": str(submitted_eval.get("evaluated_at", ""))[:100],
                        "input_fingerprint": current_fp,
                        "platform": evaluation_state["platform"],
                        "content_profile": evaluation_state["content_profile"],
                        "target_audience": evaluation_state["target_audience"],
                        "target_duration_seconds": evaluation_state["target_duration_seconds"],
                        "video_filename": out_filename,
                    }
                    eval_path = os.path.join(topic_dir, "evaluation.json")
                    with open(eval_path, "w", encoding="utf-8") as f:
                        json.dump(safe_eval, f, ensure_ascii=False, indent=2)
                    evaluation_file_saved = True

        import urllib.parse
        encoded_folder = urllib.parse.quote(folder_name)
        encoded_file = urllib.parse.quote(out_filename)
        
        res_data = {
            "success": True,
            "folder_name": folder_name,
            "folder_path": f"output/{folder_name}/",
            "video_url": f"/output/{encoded_folder}/{encoded_file}",
            "caption_url": f"/output/{encoded_folder}/caption.txt",
            "filename": out_filename,
            "caption": caption_content,
            "duration": total_duration
        }
        if evaluation_file_saved:
            res_data["evaluation_url"] = f"/output/{encoded_folder}/evaluation.json"

        return res_data
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
        if full_path.suffix == ".mp4":
            media_type = "video/mp4"
        elif full_path.suffix == ".json":
            media_type = "application/json"
        else:
            media_type = "text/plain; charset=utf-8"
        return FileResponse(full_path, media_type=media_type)
    raise HTTPException(status_code=404, detail="File not found")


if __name__ == "__main__":
    uvicorn.run("web.app:app", host="127.0.0.1", port=8001)
