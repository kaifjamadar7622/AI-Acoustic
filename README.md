---
title: Acoustic Artistry
emoji: 🎤
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "4.44.1"
python_version: "3.10"
app_file: app.py
pinned: false
---

# Acoustic Artistry

Acoustic Artistry is a Gradio application that combines two workflows:

1. Voice-to-image generation with Stable Diffusion
2. Multi-agent web research with report writing and critique

The app is designed for local usage and Hugging Face Spaces free-tier deployment.

## Features

- Voice recording and speech-to-text prompt extraction
- Prompt enhancement before image generation
- Stable Diffusion image generation
- Local account system (signup/signin) with per-user history
- Multi-agent research pipeline (search, read, write, critique)

## Project Structure

- `app.py`: main entrypoint, startup configuration, and app launch
- `ui.py`: Gradio UI layout and event wiring
- `storage.py`: user auth and SQLite-backed history persistence
- `research_agents.py`: research pipeline orchestration
- `requirements.txt`: pinned dependencies for local and Spaces runtime
- `.env.example`: required and optional environment variables

## Requirements

- Python 3.10+
- `ffmpeg` available on system path (for robust audio handling)

## Quick Start (Local)

1. Clone and enter the project directory.

```bash
git clone https://github.com/<your-username>/AI-Acoustic.git
cd AI-Acoustic/AcousticArtistry
```

2. Create and activate a virtual environment.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Copy environment template and set keys.

```bash
copy .env.example .env
```

5. Run the app.

```bash
python app.py
```

## Environment Variables

Required for image generation:

- `HF_TOKEN`: Hugging Face token with access to the selected SD model

Required for research tab:

- `OPENAI_API_KEY`: OpenAI key for writer/critic/model steps
- `TAVILY_API_KEY`: Tavily key for web search

Optional:

- `SD_MODEL_ID`: override default Stable Diffusion model
- `PROMPT_MODEL_ID`: override prompt enhancement model
- `GRADIO_SHARE`: set `true` to force share link locally

## Hugging Face Spaces Deployment

1. Create a new Gradio Space.
2. Push this folder contents to the Space repository.
3. In Space settings, add secrets:
   - `HF_TOKEN`
   - `OPENAI_API_KEY` (if using Research tab)
   - `TAVILY_API_KEY` (if using Research tab)
4. Ensure `requirements.txt` and this README metadata remain in sync.

## Notes

- User history is stored in `data/acoustic_artistry.db`.
- Generated images are saved under `data/generated/<username>/`.
- Guest generation is supported, but history is saved only for authenticated users.



