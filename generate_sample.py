import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import time
import asyncio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.script_ai import get_presets
from core.tts_engine import build_dialogue_timeline, mix_master_audio
from core.video_composer import VideoComposer
from core.character_registry import get_matchup

def main():
    print("=== OMOSHIROI COURTROOM & PARABLE SHORT TEST ===")
    
    # 1. Choose Preset Script (Sushi Terrorist Courtroom Drama)
    preset = get_presets()[0] # sushi_terrorist
    matchup = get_matchup(preset.get("matchup", "courtroom"))
    print(f"Matchup: {matchup['title']}")
    print(f"Title: {preset['title_main']} - {preset['title_sub']}")
    print(f"Moral Lesson: {preset.get('moral_lesson')}")
    for line in preset["dialogue"]:
        print(f"  [{line['speaker']} - {line['emotion']}]: {line['text']}")
        
    # 2. TTS Generation & Audio Timeline
    print("\n[Step 1/3] Generating Edge-TTS voices & audio timeline...")
    temp_dir = os.path.join(BASE_DIR, "temp_scratch", "sample_run")
    os.makedirs(temp_dir, exist_ok=True)
    
    timeline, total_duration = asyncio.run(
        build_dialogue_timeline(preset["dialogue"], temp_dir=temp_dir, default_rate="+6%")
    )
    print(f"Generated {len(timeline)} voice clips. Total duration: {total_duration:.2f}s")
    
    # 3. Audio Mixing
    print("\n[Step 2/3] Mixing dialogue with Gavel SFX, Stamp SFX, and BGM...")
    audio_dir = os.path.join(BASE_DIR, "assets", "audio")
    bgm_path = os.path.join(audio_dir, "bgm_comical.wav")
    sfx_pop = os.path.join(audio_dir, "sfx_pop.wav")
    sfx_punch = os.path.join(audio_dir, "sfx_punchline.wav")
    sfx_gavel = os.path.join(audio_dir, "sfx_gavel.wav")
    sfx_stamp = os.path.join(audio_dir, "sfx_stamp.wav")
    master_wav = os.path.join(temp_dir, "master_audio.wav")
    
    mix_master_audio(
        timeline=timeline,
        total_duration=total_duration,
        bgm_path=bgm_path,
        sfx_pop_path=sfx_pop,
        sfx_punch_path=sfx_punch,
        out_wav_path=master_wav,
        bgm_vol=0.15,
        intro_sfx_path=sfx_gavel,
        stamp_sfx_path=sfx_stamp
    )
    print(f"Master audio mixed: {master_wav}")
    
    # 4. Video Rendering
    print("\n[Step 3/3] Rendering 1080x1920 MP4 video with Chubby Judge Cat, Gavel, Red Stamp & Moral Card...")
    out_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(out_dir, exist_ok=True)
    output_mp4 = os.path.join(out_dir, "sample_courtroom_parable.mp4")
    
    assets_dir = os.path.join(BASE_DIR, "assets")
    composer = VideoComposer(assets_dir=assets_dir)
    composer.render_video(
        timeline=timeline,
        total_duration=total_duration,
        master_audio_path=master_wav,
        output_mp4=output_mp4,
        title_main=preset["title_main"],
        title_sub=preset["title_sub"],
        bg_name=matchup.get("default_bg", "courtroom"),
        moral_lesson=preset.get("moral_lesson"),
        speaker_a_id=matchup.get("speaker_a", "judge"),
        speaker_b_id=matchup.get("speaker_b", "prisoner"),
        has_mascot=matchup.get("has_mascot", True)
    )
    
    print("\n=== SUCCESS! ===")
    print(f"File created: {output_mp4}")
    print(f"Size: {os.path.getsize(output_mp4):,} bytes")

if __name__ == "__main__":
    main()
