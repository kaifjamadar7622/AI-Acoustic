🎨 Acoustic Artistry - Voice to Image Generator

Created by Kaif Jamadar.

This project uses Gradio, SpeechRecognition, and Stable Diffusion to generate AI images from your voice input.

Features
- Record audio using your microphone
- Transcribe the speech to text
- Generate an image from the transcribed text using Stable Diffusion

 Installation
1. Clone the repository:
   git clone https://github.com/your-username/voice-to-image-generator.git
   cd voice-to-image-generator
   
2. Install dependencies:
   pip install -r requirements.txt
   
3. Run the app:
   python app.py

Setup notes
- If the Stable Diffusion model download is blocked, set `HF_TOKEN` or `HUGGINGFACE_HUB_TOKEN` to a Hugging Face access token that has permission to use `CompVis/stable-diffusion-v1-4`.
- The app now uses a GenAI prompt enhancer with `google/flan-t5-base`. If that model is unavailable, it falls back to local prompt expansion.
- No API key is required for speech recognition; the app uses Google's public speech-to-text endpoint through `SpeechRecognition`.
- Make sure microphone access is allowed in the browser when you open Gradio.
- If you generate a custom UI with Claude, paste it into [ui.py](ui.py). Keep the `create_genai_result(...)` function call signature the same so the UI remains connected to the backend.
- The app now includes local sign up, sign in, and per-user generation history.
- Logged-in users get their generation records saved in `data/acoustic_artistry.db`.
- Generated image files are stored under `data/generated/<username>/`.
- You can generate as a guest without signing in; history is only saved for logged-in users.
- The app is tuned for free-tier hosting with fast defaults and optional prompt enhancement.

Recommended free-tier deployment
1. Push this repo to GitHub.
2. Create a Hugging Face Space using the Gradio SDK.
3. Connect your GitHub repo or upload the files.
4. Add `HF_TOKEN` as a secret in Space settings.
5. Deploy on ZeroGPU or the free shared hardware option.
6. Use the Create tab to generate, the Account tab to save work, and the History tab to review past runs.

Deployment note
- The local SQLite history is best for temporary or small-scale free-tier deployments. For persistent cloud-wide history, you would move to a hosted database later.

Publish this project to your GitHub repo
1. Create an empty repository on GitHub (without README/license/gitignore) with your preferred name.
2. In this project folder, run:
   git add .
   git commit -m "Initial commit - Acoustic Artistry by Kaif Jamadar"
3. Add your GitHub remote:
   git remote add origin https://github.com/<your-username>/<your-repo>.git
4. Push to GitHub:
   git branch -M main
   git push -u origin main



