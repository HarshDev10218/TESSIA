import io
from gtts import gTTS

def text_to_speech(text, voice_id=None):
    """
    Converts text to MP3 audio bytes using Google Text-to-Speech (gTTS).
    100% free, no API keys required.
    """
    if not text or not text.strip():
        return None, "Empty text provided"

    try:
        # Generate speech audio using Google Translate's TTS engine
        tts = gTTS(text=text, lang='en', tld='com')
        
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        return fp.read(), None
    except Exception as e:
        print(f"[gTTS Error]: {str(e)}")
        return None, f"Google TTS Error: {str(e)}"


def speech_to_text(audio_bytes, mime_type="audio/webm"):
    """
    Placeholder for server-side STT.
    For listening, Chrome's native Web Speech API (Google Speech engine)
    in the browser is recommended.
    """
    return None, "Server STT not configured. Use browser native recognition."