import asyncio
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


sys.modules.setdefault("edge_tts", types.ModuleType("edge_tts"))
from core import tts_engine
from core.caption_generator import resolve_output_file, sanitize_folder_name
from core.character_registry import DUO_MATCHUPS
from core.script_ai import get_presets
from core.script_ai import generate_script_from_prompt
from core.video_composer import fit_font_to_width, layout_subtitles


class StudioSmokeTests(unittest.TestCase):
    def test_selected_voice_rate_reaches_tts(self):
        rates = []

        async def fake_synthesize(text, voice, out_path, rate, pitch):
            rates.append(rate)

        dialogue = [{"speaker": "judge", "text": "こんにちは", "emotion": "normal"}]
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(tts_engine, "synthesize_line", fake_synthesize), patch.object(
                tts_engine, "get_audio_duration", return_value=1.0
            ):
                asyncio.run(tts_engine.build_dialogue_timeline(dialogue, temp_dir, "+12%"))
        self.assertEqual(rates, ["+12%"])

    def test_missing_ffmpeg_is_added_from_project_dependency(self):
        calls = []
        fake = types.ModuleType("static_ffmpeg")
        fake.add_paths = lambda weak: calls.append(weak)
        with patch("shutil.which", return_value=None), patch.dict(sys.modules, {"static_ffmpeg": fake}):
            tts_engine.ensure_ffmpeg()
        self.assertEqual(calls, [True])

    def test_output_download_stays_inside_output_folder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "output"
            output.mkdir()
            video = output / "sample.mp4"
            video.write_bytes(b"video")
            (root / "secret.txt").write_text("private")
            self.assertEqual(resolve_output_file(output, "sample.mp4"), video)
            self.assertIsNone(resolve_output_file(output, "../secret.txt"))
            self.assertIsNone(resolve_output_file(output, "missing.mp4"))

    def test_long_title_produces_windows_safe_output_name(self):
        name = sanitize_folder_name("a" * 300 + "\n?")
        self.assertLessEqual(len(name), 80)
        self.assertNotIn("\n", name)
        self.assertNotIn("?", name)

    def test_presets_use_rendered_matchup_characters(self):
        matchups = {matchup["id"]: matchup for matchup in DUO_MATCHUPS}
        for preset in get_presets():
            with self.subTest(preset=preset["id"]):
                matchup = matchups[preset["matchup"]]
                rendered = {matchup["speaker_a"], matchup["speaker_b"]}
                self.assertEqual({line["speaker"] for line in preset["dialogue"]}, rendered)

    def test_gemini_request_uses_supported_sdk_and_model(self):
        calls = []

        class FakeClient:
            def __init__(self, api_key):
                calls.append(("key", api_key))
                self.models = self

            def generate_content(self, model, contents):
                calls.append(("model", model))
                calls.append(("prompt", contents))
                return types.SimpleNamespace(text='{"title_sub":"AI result","dialogue":[]}')

        google = types.ModuleType("google")
        genai = types.ModuleType("google.genai")
        genai.Client = FakeClient
        google.genai = genai
        with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
            result = generate_script_from_prompt("unlisted custom topic", api_key="test-key")
        self.assertEqual(result["title_sub"], "AI result")
        self.assertEqual(result["generation_mode"], "gemini")
        self.assertEqual(calls[:2], [("key", "test-key"), ("model", "gemini-3.6-flash")])
        self.assertIn("【裁判】○○の末路", calls[2][1])
        self.assertNotIn("【Tòa Án Kỳ Án】", calls[2][1])

    def test_offline_generation_identifies_template_fallback(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            result = generate_script_from_prompt("nhân viên trễ deadline", matchup_id="koban", api_key="")
        self.assertEqual(result["generation_mode"], "offline")
        self.assertEqual(result["id"], "cosme_shoplifting")
        self.assertNotIn("nhân viên", result["title_sub"])
        self.assertTrue(all("nhân viên" not in line["text"] for line in result["dialogue"]))

    def test_rejected_gemini_key_is_reported_without_exposing_key(self):
        class FakeClient:
            def __init__(self, api_key):
                self.models = self

            def generate_content(self, model, contents):
                error = RuntimeError("SECRET-KEY was rejected")
                error.code = 403
                raise error

        google = types.ModuleType("google")
        genai = types.ModuleType("google.genai")
        genai.Client = FakeClient
        google.genai = genai
        with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
            with self.assertRaises(Exception) as caught:
                generate_script_from_prompt("nhân viên trễ deadline", api_key="SECRET-KEY")
        self.assertIn("403", str(caught.exception))
        self.assertNotIn("SECRET-KEY", str(caught.exception))

    def test_gemini_uses_lite_model_when_flash_is_unavailable(self):
        models = []

        class FakeClient:
            def __init__(self, api_key):
                self.models = self

            def generate_content(self, model, contents):
                models.append(model)
                if len(models) == 1:
                    error = RuntimeError("unavailable")
                    error.code = 503
                    raise error
                return types.SimpleNamespace(text='{"title_sub":"AI result","dialogue":[]}')

        google = types.ModuleType("google")
        genai = types.ModuleType("google.genai")
        genai.Client = FakeClient
        google.genai = genai
        with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
            result = generate_script_from_prompt("nhân viên trễ deadline", api_key="test-key")
        self.assertEqual(result["generation_mode"], "gemini")
        self.assertEqual(models, ["gemini-3.6-flash", "gemini-3.5-flash-lite"])

    def test_generate_api_returns_safe_gemini_error(self):
        from fastapi.testclient import TestClient
        from core.script_ai import GeminiGenerationError
        from web.app import app

        with patch("web.app.generate_script_from_prompt", side_effect=GeminiGenerationError("Gemini từ chối quyền truy cập (403).")):
            response = TestClient(app).post("/api/generate_ai", json={"topic": "test", "api_key": "SECRET-KEY"})
        self.assertEqual(response.status_code, 502)
        self.assertIn("403", response.json()["detail"])
        self.assertNotIn("SECRET-KEY", response.text)

    def test_preset_titles_and_subtitles_fit_video(self):
        title_font_path = "assets/fonts/font_dela.ttf"
        sub_font_path = "assets/fonts/font_zenmaru.ttf"
        for preset in get_presets():
            with self.subTest(preset=preset["id"]):
                title_font = fit_font_to_width(title_font_path, preset["title_sub"], 960, 60)
                self.assertLessEqual(title_font.getlength(preset["title_sub"]), 960)
                for line in preset["dialogue"]:
                    parsed, _, _ = layout_subtitles(line["text"], sub_font_path)
                    for tokens, font in parsed:
                        self.assertLessEqual(font.getlength("".join(tokens)), 900)


    def test_regret_emotion_sprites_exist_and_load(self):
        from core.video_composer import VideoComposer
        from core.character_registry import CHARACTERS
        
        composer = VideoComposer(assets_dir="assets")
        for char_id in CHARACTERS.keys():
            sprite = composer.get_character_sprite(char_id, "regret")
            self.assertIsNotNone(sprite)
            self.assertGreater(sprite.width, 0)
            self.assertGreater(sprite.height, 0)


if __name__ == "__main__":
    unittest.main()
