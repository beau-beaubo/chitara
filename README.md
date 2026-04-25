# Chitara
Chitara is an AI-powered music generation platform. This repo contains the Django backend/domain layer for **Users** and **Songs**, plus Exercise 4’s Strategy-based song generation (Mock vs Suno).

## Exercise implemented detail
- docs/Exercise3.md
- docs/Exercise4.md
- diagram/classdiagram.png
- diagram/domainmodel.png
- diagram/sequencediagram.png

## Prerequisites

- Python 3.11+
- A Google account (for OAuth)
- A Suno API account (for real AI generation — optional, mock works offline)

---

## 1. Clone & Install

```bash
git clone <repo-url>
cd chitara/backend
pip install -r requirements.txt
```

---

## 2. Environment Variables

Copy the example and fill in your secrets:

```bash
cp .env.example .env   # or edit .env directly
```

Key variables in `.env`:

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key | `django-insecure-xxx` |
| `DEBUG` | Enable debug mode | `True` |
| `FRONTEND_ORIGIN` | Where the frontend is served | `http://localhost:8000` |
| `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY` | Google OAuth Client ID | `427558...apps.googleusercontent.com` |
| `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET` | Google OAuth Client Secret | `GOCSPX-...` |
| `GENERATOR_STRATEGY` | `mock` (offline) or `suno` (real AI) | `mock` |
| `SUNO_API_KEY` | Your Suno API key | `abc123...` |

---

## 3. Google OAuth Setup

### Step 1 — Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"New Project"** → give it a name (e.g. `chitara`) → **Create**

### Step 2 — Enable Google+ / Identity API

1. In the sidebar: **APIs & Services → Library**
2. Search for **"Google Identity"** or **"Google+ API"** → **Enable**

### Step 3 — Create OAuth Credentials

1. **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
2. Application type: **Web application**
3. Name: `Chitara Dev`
4. Under **Authorised redirect URIs** add:
   ```
   http://localhost:8000/api/auth/google/callback/
   ```
5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

### Step 4 — Configure OAuth Consent Screen

1. **APIs & Services → OAuth consent screen**
2. User type: **External** → **Create**
3. Fill in:
   - App name: `Chitara`
   - User support email: your email
   - Developer contact: your email
4. Scopes: add `email` and `openid`
5. Test users: add your own Google email
6. Save

### Step 5 — Add to `.env`

```env
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=<your-client-id>.apps.googleusercontent.com
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=<your-client-secret>
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI=http://localhost:8000/api/auth/google/callback/
FRONTEND_ORIGIN=http://localhost:8000
```

### Step 6 — Test the OAuth Flow

1. Start the server: `python manage.py runserver`
2. Open `http://localhost:8000`
3. Click **"Continue with Google"**
4. You should be redirected to Google → choose an account → redirected back with a JWT token

---

## 4. Suno API Setup (for real AI song generation)

By default the app uses `GENERATOR_STRATEGY=mock` which generates a short test tone (offline, no API key needed). Switch to `suno` for real AI-generated music.

### Step 1 — Get a Suno API Key

1. Go to [sunoapi.org](https://sunoapi.org) and create an account
2. Navigate to **Dashboard → API Keys → Create Key**
3. Copy your API key

### Step 2 — Add to `.env`

```env
GENERATOR_STRATEGY=suno
SUNO_API_KEY=<your-suno-api-key>
SUNO_API_BASE_URL=https://api.sunoapi.org/api/v1
SUNO_MODEL=V4_5ALL
SUNO_CUSTOM_MODE=false
SUNO_INSTRUMENTAL=false
```

| Variable | Options | Description |
|---|---|---|
| `SUNO_MODEL` | `V4_5ALL`, `V4_5`, `V4`, `V3_5` | Generation model version |
| `SUNO_CUSTOM_MODE` | `true` / `false` | Custom vs. auto mode |
| `SUNO_INSTRUMENTAL` | `true` / `false` | Generate without vocals |
| `SUNO_CALLBACK_URL` | any HTTPS URL | Webhook for async completion (optional) |
| `SUNO_HTTP_TIMEOUT_SECONDS` | integer | HTTP request timeout (default `30`) |

### Step 3 — How Generation Works with Suno

1. Click **⚡ Generate** on a song card
2. The backend sends your prompt to Suno → returns a `taskId` (status: `Processing`)
3. The frontend polls `GET /api/songs/{id}/generate/` every 3 seconds
4. When Suno finishes, status becomes `Completed` and the audio URL is saved
5. The **▶ Play** and **↓ Download** buttons appear

> **Note:** Suno generation typically takes 20–60 seconds depending on model and server load.

### Step 4 — Fallback to Mock

If you want to test the UI without spending Suno credits, set:

```env
GENERATOR_STRATEGY=mock
```

The mock generator instantly returns a 1.5-second 440Hz sine wave (`audio/wav`) so you can test the full Play → Download → Share flow offline.

---

## 5. Database Setup

```bash
cd backend
python manage.py migrate          # apply all migrations
python manage.py seed_tags        # seed Genre/Mood/Occasion tags
python manage.py createsuperuser  # (optional) create an admin account
```

---

## 6. Run the Development Server

```bash
python manage.py runserver
```

Open **http://localhost:8000** — Django serves the frontend directly from the `frontend/` folder.

---