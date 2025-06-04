# Vocality-Nexus

## Overview

The Vocal Mirror tool architecture consists of the following main modules:

### Frontend (React + Ionic + TailwindCSS + Framer Motion + Shadcn/UI)
- **Audio Capture & Processing**
  - Uses Web Audio API, Tone.js, Meyda.js for real-time audio feature extraction (pitch, timbre, intensity, rhythm, clarity).
- **Emotion Detection**
  - TensorFlow.js, Whisper, Onnx.js, Vosk.js models running locally for emotion classification.
- **Visualization**
  - Dynamic pitch curve, spectrogram, emotional bar visualizations with accessible colors and animations.
- **AI Tuning**
  - Adaptive tuning controls with automatic and manual modes.
- **Recording & Playback**
  - WaveSurfer.js for waveform visualization, recording in WAV/OGG, A/B sync playback.
- **Export & Sharing**
  - ffmpeg.wasm for video export with audio, visualizations, subtitles.
  - Sharing integration with Discord, Twitch, YouTube Shorts.

### Backend (Supabase + Socket.IO)
- **Authentication**
  - Supabase Auth for user management.
- **Database & Storage**
  - Supabase DB for session metadata.
  - Supabase Storage for encrypted recordings.
- **Real-time Communication**
  - Socket.IO server for live data sync and control messages.

### Security & Privacy
- Local processing by default.
- AES-256 encryption for recordings.
- Anonymity options with avatars and nicknames.

### Deployment
- PWA and native app compatibility.
- WebSocket support for Discord and OBS integration.

## Diagram

```
+-------------------+       +-------------------+       +-------------------+
|                   |       |                   |       |                   |
|   Frontend App    <------->  Socket.IO Server <------->  Supabase Backend  |
| (React + Audio &  |       | (Real-time comm)  |       | (Auth, DB, Storage)|
|  AI Modules)      |       |                   |       |                   |
+-------------------+       +-------------------+       +-------------------+

Frontend Modules:
- Audio Capture & Processing
- Emotion Detection
- Visualization Panels
- AI Tuning Controls
- Recording & Playback
- Export & Sharing

Backend Modules:
- User Authentication
- Session Metadata Storage
- Encrypted Recording Storage
- Real-time Communication Server

External Integrations:
- Discord, Twitch, YouTube APIs
- OBS WebSocket
```

This diagram and overview will guide the modular development of the Vocal Mirror tool.
