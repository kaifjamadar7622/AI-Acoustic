import os
from functools import lru_cache

import speech_recognition as sr
from storage import save_generation_assets, save_generation_history

IMAGE_MODEL_ID = os.getenv("SD_MODEL_ID", "CompVis/stable-diffusion-v1-4")
PROMPT_MODEL_ID = os.getenv("PROMPT_MODEL_ID", "").strip() or None
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")

STYLE_PRESETS = {
    "Cinematic Photoreal": "cinematic lighting, ultra-detailed, realistic textures, shallow depth of field, dramatic composition",
    "Anime Illustration": "clean anime linework, vibrant colors, expressive character design, polished illustration",
    "Editorial Poster": "bold typography-friendly composition, graphic design, strong contrast, modern poster aesthetics",
    "Concept Art": "environment concept art, atmospheric perspective, rich detail, matte painting quality",
    "Product Shot": "studio lighting, premium product photography, crisp shadows, clean background",
}

NEGATIVE_BASE = (
    "blurry, low resolution, distorted anatomy, extra fingers, extra limbs, watermark, text, "
    "duplicate, noisy, oversaturated, cropped, jpeg artifacts"
)


def _load_pretrained_pipeline(model_id, **kwargs):
    from diffusers import StableDiffusionPipeline

    try:
        return StableDiffusionPipeline.from_pretrained(model_id, **kwargs)
    except TypeError:
        token = kwargs.pop("token", None)
        if token:
            return StableDiffusionPipeline.from_pretrained(model_id, use_auth_token=token, **kwargs)
        return StableDiffusionPipeline.from_pretrained(model_id, **kwargs)


def _get_torch():
    import torch

    return torch


@lru_cache(maxsize=1)
def get_device():
    torch = _get_torch()
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=1)
def load_image_pipeline():
    torch = _get_torch()
    device = get_device()

    load_kwargs = {}
    if HF_TOKEN:
        load_kwargs["token"] = HF_TOKEN
    load_kwargs["torch_dtype"] = torch.float16 if device == "cuda" else torch.float32

    pipeline = _load_pretrained_pipeline(IMAGE_MODEL_ID, **load_kwargs)
    pipeline = pipeline.to(device)
    pipeline.enable_attention_slicing()
    return pipeline


@lru_cache(maxsize=1)
def load_prompt_pipeline():
    if not PROMPT_MODEL_ID:
        return None

    from transformers import pipeline as hf_pipeline

    device = get_device()
    try:
        return hf_pipeline(
            "text2text-generation",
            model=PROMPT_MODEL_ID,
            device=0 if device == "cuda" else -1,
        )
    except Exception:
        return None


def recognize_speech(audio_file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"Recognized: {text}")
        return text
    except sr.UnknownValueError:
        print("Speech recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
    return None


def expand_prompt(transcript, style_name, extra_instructions=""):
    style_description = STYLE_PRESETS.get(style_name, STYLE_PRESETS["Cinematic Photoreal"])
    prompt_model = load_prompt_pipeline()
    extra = extra_instructions.strip()

    if not prompt_model:
        parts = [
            f"{transcript.strip()}",
            style_description,
            "high quality, detailed composition, soft cinematic lighting, polished image, artistic depth",
        ]
        if extra:
            parts.append(extra)
        return ", ".join(part for part in parts if part)

    if prompt_model:
        instruction = (
            "Rewrite this spoken idea into a rich image prompt. "
            f"Style: {style_name}. Visual direction: {style_description}. "
            f"Voice note: {transcript}. "
            f"Additional instructions: {extra or 'none'}. "
            "Return only the final prompt."
        )
        try:
            result = prompt_model(instruction, max_new_tokens=96, do_sample=True, temperature=0.7, top_p=0.9)
            refined = result[0]["generated_text"].strip()
            if refined:
                return refined
        except Exception:
            pass

    parts = [transcript.strip(), style_description]
    if extra:
        parts.append(extra)
    return ", ".join(part for part in parts if part)


def build_negative_prompt(style_name):
    style_hints = {
        "Cinematic Photoreal": "cartoon, illustration, low contrast",
        "Anime Illustration": "photorealistic skin, noisy background",
        "Editorial Poster": "messy layout, unreadable text, dull composition",
        "Concept Art": "flat lighting, boring environment",
        "Product Shot": "busy background, crooked framing, harsh glare",
    }
    return f"{NEGATIVE_BASE}, {style_hints.get(style_name, 'low detail, poor composition')}"


def generate_images(prompt, negative_prompt, steps, guidance_scale, seed, image_count, width, height):
    torch = _get_torch()
    device = get_device()

    pipeline = load_image_pipeline()
    generator = None
    if seed not in (None, ""):
        generator = torch.Generator(device=device).manual_seed(int(seed))

    generation_kwargs = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "num_inference_steps": int(steps),
        "guidance_scale": float(guidance_scale),
        "num_images_per_prompt": int(image_count),
        "width": int(width),
        "height": int(height),
    }
    if generator is not None:
        generation_kwargs["generator"] = generator

    if device == "cuda":
        with torch.autocast("cuda"):
            result = pipeline(**generation_kwargs)
    else:
        result = pipeline(**generation_kwargs)

    return result.images


def create_genai_result(audio_file_path, style_name, extra_instructions, steps, guidance_scale, seed, image_count, width, height, username=""):
    transcript = recognize_speech(audio_file_path)
    if not transcript:
        return "No speech recognized", "", "", [], audio_file_path, "Try speaking more clearly or upload a cleaner clip."

    prompt = expand_prompt(transcript, style_name, extra_instructions)
    negative_prompt = build_negative_prompt(style_name)

    try:
        images = generate_images(prompt, negative_prompt, steps, guidance_scale, seed, image_count, width, height)
        status = f"Generated {len(images)} image(s) on {get_device()}."
        user_key = (username or "").strip() or "anonymous"
        saved_paths = save_generation_assets(user_key, images)
        if user_key != "anonymous":
            save_generation_history(
                user_key,
                transcript,
                prompt,
                negative_prompt,
                style_name,
                saved_paths,
                audio_file_path,
                status,
            )
    except Exception as exc:
        return transcript, prompt, negative_prompt, [], audio_file_path, f"Image generation failed: {exc}"

    return transcript, prompt, negative_prompt, images, audio_file_path, status


if __name__ == "__main__":
    from ui import build_ui

    port = int(os.getenv("PORT", "7860"))
    is_space = bool(os.getenv("SPACE_ID"))
    if is_space:
        # Spaces runtime hits Gradio's API schema route during startup. Disable it in-place.
        import gradio.blocks
        import gradio.routes

        gradio.routes.api_info = lambda include_str=False: {}
        gradio.blocks.Blocks.get_api_info = lambda self: {}

        build_ui().launch(
            server_name="0.0.0.0",
            server_port=port,
            share=False,
            show_api=False,
        )
    else:
        build_ui().launch(
            server_name="0.0.0.0",
            server_port=port,
            share=False,
            show_api=False,
        )
