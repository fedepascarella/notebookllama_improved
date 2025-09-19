#!/usr/bin/env python3
"""
Test script to verify ElevenLabs API functionality
"""

import asyncio
import os
from dotenv import load_dotenv
from elevenlabs import AsyncElevenLabs
import tempfile

async def test_elevenlabs():
    """Test basic ElevenLabs functionality"""

    # Load environment variables
    load_dotenv()

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("ELEVENLABS_API_KEY not found in environment")
        return False

    print(f"ElevenLabs API key found: {api_key[:10]}...")

    try:
        # Initialize client
        client = AsyncElevenLabs(api_key=api_key)
        print("ElevenLabs client initialized")

        # Test 1: List available voices
        try:
            voices = await client.voices.get_all()
            print(f"Available voices: {len(voices.voices)} found")

            for i, voice in enumerate(voices.voices[:3]):  # Show first 3
                print(f"   Voice {i+1}: {voice.name} (ID: {voice.voice_id})")

        except Exception as e:
            print(f"Failed to get voices: {e}")
            return False

        # Test 2: Generate simple speech
        test_text = "Hello, this is a test of ElevenLabs text-to-speech functionality."
        voice_id = voices.voices[0].voice_id  # Use first available voice

        print(f"\nTesting speech generation with voice: {voices.voices[0].name}")

        try:
            speech_iterator = client.text_to_speech.convert(
                voice_id=voice_id,
                text=test_text,
                output_format="mp3_22050_32",
                model_id="eleven_turbo_v2_5",
            )

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                chunk_count = 0
                async for chunk in speech_iterator:
                    if chunk:
                        temp_file.write(chunk)
                        chunk_count += 1

                temp_file_path = temp_file.name

            # Check file size
            file_size = os.path.getsize(temp_file_path)
            print(f"Speech generated successfully!")
            print(f"   File: {temp_file_path}")
            print(f"   Size: {file_size} bytes")
            print(f"   Chunks: {chunk_count}")

            # Clean up
            os.unlink(temp_file_path)

            return True

        except Exception as e:
            print(f"Speech generation failed: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return False

    except Exception as e:
        print(f"ElevenLabs client initialization failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("Testing ElevenLabs API functionality...\n")

    success = asyncio.run(test_elevenlabs())

    if success:
        print("\nAll tests passed! ElevenLabs is working correctly.")
    else:
        print("\nTests failed. Check your API key and internet connection.")