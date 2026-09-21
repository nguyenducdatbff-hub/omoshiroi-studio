import asyncio
import edge_tts
import subprocess
import os
import shutil
import wave
import numpy as np
from core.character_registry import get_character

def ensure_ffmpeg():
    if shutil.which('ffmpeg') and shutil.which('ffprobe'):
        return
    import static_ffmpeg
    static_ffmpeg.add_paths(weak=True)

def get_audio_duration(file_path):
    ensure_ffmpeg()
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

async def synthesize_line(text, voice, out_path, rate='+0%', pitch='+0Hz'):
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(out_path)

async def build_dialogue_timeline(dialogue, temp_dir='scratch_audio', default_rate='+6%'):
    os.makedirs(temp_dir, exist_ok=True)
    timeline = []
    current_time = 0.6  # 0.6s initial pause for intro gavel strike
    
    for idx, item in enumerate(dialogue):
        speaker = item.get('speaker', 'judge')
        text = item.get('text', '')
        emotion = item.get('emotion', 'normal')
        
        char_conf = get_character(speaker)
        voice = char_conf.get('voice', 'ja-JP-KeitaNeural')
        pitch = item.get('pitch', char_conf.get('pitch', '+0Hz'))
        rate = item.get('rate') or default_rate
        
        audio_file = os.path.join(temp_dir, f'line_{idx:02d}_{speaker}.mp3')
        await synthesize_line(text, voice, audio_file, rate=rate, pitch=pitch)
        
        dur = get_audio_duration(audio_file)
        
        timeline.append({
            'index': idx,
            'speaker': speaker,
            'text': text,
            'emotion': emotion,
            'start': current_time,
            'end': current_time + dur,
            'duration': dur,
            'audio_file': audio_file
        })
        
        # 0.3s pause between lines for comedic & dramatic timing
        current_time += dur + 0.30
        
    # Add 2.5s outro padding for Red Hanko Stamp & Moral Lesson display
    total_duration = current_time + 2.5
    return timeline, total_duration

def mix_master_audio(timeline, total_duration, bgm_path, sfx_pop_path, sfx_punch_path,
                     out_wav_path, bgm_vol=0.15, intro_sfx_path=None, stamp_sfx_path=None):
    ensure_ffmpeg()
    sample_rate = 44100
    n_samples = int(total_duration * sample_rate)
    master = np.zeros(n_samples, dtype=np.float32)
    
    # 1. Intro SFX (Gavel strike at t=0.0s)
    if intro_sfx_path and os.path.exists(intro_sfx_path):
        cmd = [
            'ffmpeg', '-v', 'error', '-y',
            '-i', intro_sfx_path,
            '-f', 's16le', '-acodec', 'pcm_s16le',
            '-ar', str(sample_rate), '-ac', '1', '-'
        ]
        res = subprocess.run(cmd, capture_output=True, check=True)
        intro_samples = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        end_idx = min(len(master), len(intro_samples))
        master[0:end_idx] += intro_samples[:end_idx] * 0.85

    # 2. Mix each character speech audio
    for item in timeline:
        cmd = [
            'ffmpeg', '-v', 'error', '-y',
            '-i', item['audio_file'],
            '-f', 's16le', '-acodec', 'pcm_s16le',
            '-ar', str(sample_rate), '-ac', '1', '-'
        ]
        res = subprocess.run(cmd, capture_output=True, check=True)
        raw_samples = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        
        start_idx = int(item['start'] * sample_rate)
        end_idx = start_idx + len(raw_samples)
        if end_idx > len(master):
            raw_samples = raw_samples[:len(master) - start_idx]
            end_idx = len(master)
            
        master[start_idx:end_idx] += raw_samples

    # 3. Mix BGM (looping across whole video)
    if bgm_path and os.path.exists(bgm_path):
        cmd = [
            'ffmpeg', '-v', 'error', '-y',
            '-i', bgm_path,
            '-f', 's16le', '-acodec', 'pcm_s16le',
            '-ar', str(sample_rate), '-ac', '1', '-'
        ]
        res = subprocess.run(cmd, capture_output=True, check=True)
        bgm_samples = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        if len(bgm_samples) > 0:
            loops = int(np.ceil(n_samples / len(bgm_samples)))
            tiled_bgm = np.tile(bgm_samples, loops)[:n_samples]
            master += tiled_bgm * bgm_vol

    # 4. Outro Stamp SFX (at total_duration - 2.4s)
    if stamp_sfx_path and os.path.exists(stamp_sfx_path):
        stamp_time = max(0.0, total_duration - 2.4)
        cmd = [
            'ffmpeg', '-v', 'error', '-y',
            '-i', stamp_sfx_path,
            '-f', 's16le', '-acodec', 'pcm_s16le',
            '-ar', str(sample_rate), '-ac', '1', '-'
        ]
        res = subprocess.run(cmd, capture_output=True, check=True)
        stamp_samples = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        start_idx = int(stamp_time * sample_rate)
        end_idx = min(len(master), start_idx + len(stamp_samples))
        master[start_idx:end_idx] += stamp_samples[:end_idx - start_idx] * 0.90

    # 5. Punchline SFX on final dialogue punchline
    if sfx_punch_path and os.path.exists(sfx_punch_path) and len(timeline) > 0:
        last_item = timeline[-1]
        cmd = [
            'ffmpeg', '-v', 'error', '-y',
            '-i', sfx_punch_path,
            '-f', 's16le', '-acodec', 'pcm_s16le',
            '-ar', str(sample_rate), '-ac', '1', '-'
        ]
        res = subprocess.run(cmd, capture_output=True, check=True)
        punch_samples = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        start_idx = int(last_item['start'] * sample_rate)
        end_idx = min(len(master), start_idx + len(punch_samples))
        master[start_idx:end_idx] += punch_samples[:end_idx - start_idx] * 0.40

    master = np.clip(master, -0.98, 0.98)
    int_master = (master * 32767).astype(np.int16)
    
    with wave.open(out_wav_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_master.tobytes())
