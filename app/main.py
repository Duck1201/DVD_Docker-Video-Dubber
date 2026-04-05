import os
os.environ["COQUI_TOS_AGREED"] = "1"

import subprocess
import whisper
from TTS.api import TTS
import argostranslate.package
import argostranslate.translate

INPUT_DIR = "/input"
OUTPUT_DIR = "/output"
TEMP_DIR = "/temp"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# 🔧 Garantir modelo de tradução
def ensure_translation_model():
    installed_languages = argostranslate.translate.get_installed_languages()

    has_en = any(l.code == "en" for l in installed_languages)
    has_pt = any(l.code == "pt" for l in installed_languages)

    if not (has_en and has_pt):
        print("⬇️ Baixando modelo en → pt...")

        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()

        package = next(
            p for p in available_packages
            if p.from_code == "en" and p.to_code == "pt"
        )

        argostranslate.package.install_from_path(package.download())


# 🎬 Processar vídeo
def process_video(video_file):
    print(f"\n🎥 Processando: {video_file}")

    video_path = os.path.join(INPUT_DIR, video_file)
    base_name = os.path.splitext(video_file)[0]

    audio_path = os.path.join(TEMP_DIR, f"{base_name}.wav")
    tts_audio = os.path.join(TEMP_DIR, f"{base_name}_tts.wav")
    final_video = os.path.join(OUTPUT_DIR, f"{base_name}_dublado.mp4")

    # 1. Extrair áudio
    print("🔊 Extraindo áudio...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ], check=True)

    # 2. Whisper
    print("🧠 Transcrevendo...")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    text_en = result["text"]

    print("EN:", text_en)

    # 3. Tradução
    print("🌐 Traduzindo...")
    installed_languages = argostranslate.translate.get_installed_languages()

    from_lang = next(l for l in installed_languages if l.code == "en")
    to_lang = next(l for l in installed_languages if l.code == "pt")

    translation = from_lang.get_translation(to_lang)
    text_pt = translation.translate(text_en)

    print("PT:", text_pt)

    # 4. TTS
    print("🗣️ Gerando voz...")
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

    tts.tts_to_file(
        text=text_pt,
        file_path=tts_audio,
        speaker_wav=audio_path,
        language="pt",
        split_sentences=True  # 👈 resolve o problema
    )

    # 5. Juntar vídeo
    print("🎬 Renderizando vídeo final...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", tts_audio,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-shortest",
        final_video
    ], check=True)

    print(f"✅ Final salvo em: {final_video}")


# 🚀 MAIN
if __name__ == "__main__":
    print("🚀 Iniciando pipeline...")

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith((".mp4", ".mkv", ".avi"))]

    if not files:
        print("❌ Nenhum vídeo encontrado em /input")
        exit(1)

    ensure_translation_model()

    for video in files:
        try:
            process_video(video)
        except Exception as e:
            print(f"❌ Erro ao processar {video}: {e}")