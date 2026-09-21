import asyncio
import edge_tts
import os

async def generate_speech(text, voice, out_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_file)

async def main():
    os.makedirs("scratch_audio", exist_ok=True)
    boy_text = "ねえ、俺のことどう思ってる？"
    girl_text = "え？生理的に無理かな！"
    
    print("Synthesizing boy voice...")
    await generate_speech(boy_text, "ja-JP-KeitaNeural", "scratch_audio/boy_test.mp3")
    print("Synthesizing girl voice...")
    await generate_speech(girl_text, "ja-JP-NanamiNeural", "scratch_audio/girl_test.mp3")
    print("Done!")

asyncio.run(main())
