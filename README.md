# Chitara (Django backend) — Exercises 3 & 4

Chitara is an AI-powered music generation platform. This repo contains the Django backend/domain layer for **Users** and **Songs**, plus Exercise 4’s Strategy-based song generation (Mock vs Suno).

## What’s implemented
- Users: custom `User` model with `external_id`
- Google OAuth login (`/auth/login/google-oauth2/`)
- Songs: `Song` model + tags (`GenreTag`, `MoodTag`, `OccasionTag`)
- Simple JSON API
- Optional Next.js + Tailwind frontend in `frontend/`
- Song generation strategies:
  - `mock` (offline, deterministic)
  - `suno` (calls SunoApi.org using Bearer token)
- Share links (`/api/songs/<id>/share/`, `/api/shared/<share_hash>/`)
- Creator-only downloads (`/api/songs/<id>/download/`)

## SRS alignment (FURPS – Functionality)

See `SRS_REQUIREMENTS_COVERAGE.md` for an FR/NFR traceability table and the calculation supporting the “80%++” claim (for the MVP scope implemented in this repo).

## Quickstart

```bash
git clone git@github.com:beau-beaubo/chitara.git
cd chitara

python3 -m venv .venv
source .venv/bin/activate

pip install -r backend/requirements.txt

# Optional but recommended: create a local .env for configuration (kept out of git)
cp .env.example .env

cd backend
python3 manage.py migrate
python3 manage.py seed_tags
python3 manage.py createsuperuser
python3 manage.py runserver
```

Base URL: `http://127.0.0.1:8000`
- Frontend: `http://localhost:8000/`
- Backend API: `http://localhost:8000/api`


Notes:

- Backend runs with `gunicorn` and auto-runs `migrate` + `seed_tags` on startup.
- SQLite is persisted in a named Docker volume (`backend_data`).
- For Google OAuth in containers, set OAuth redirect URI to:
  - `http://localhost:8000/auth/complete/google-oauth2/`


## Placeholders used below

- `SONG_ID`: numeric song id

If you see a 404 like **“No Song matches the given query.”**, it means that `SONG_ID` does not exist in your database.

## Exercise 3 — Songs CRUD (JSON API)

All songs endpoints are authenticated and creator-scoped.
Use the frontend login button (Google OAuth) or an authenticated Django session.

### Create (POST)

Required fields:

- `title`
- `prompt_text`
- `voice_type`

Other fields you see in Django Admin (like `file_path`, `generation_task_id`, `status`, tags, etc.) are either optional, have defaults, or are populated later when you call the generation endpoint.

```bash
curl -X POST http://127.0.0.1:8000/api/songs/ \
  -H 'Content-Type: application/json' \
  -d '{"title":"My First Song","prompt_text":"lofi chill beat","voice_type":"female"}'
```

Optional fields you can include on create (examples):

- `status` (defaults to `Pending`)
- `duration` (stored on the `Song` as integer seconds)
- `is_shared` (defaults to `false`)
- `share_hash` (optional)
- `genre_ids`, `mood_ids`, `occasion_ids` (arrays of existing tag ids)

```bash
curl -X POST http://127.0.0.1:8000/api/songs/ \
  -H 'Content-Type: application/json' \
  -d '{"title":"Demo Song","prompt_text":"lofi chill beat","voice_type":"female","status":"Pending","duration":120,"is_shared":false,"genre_ids":[1],"mood_ids":[1],"occasion_ids":[1]}'
```

To quickly see available tag ids:

```bash
cd backend && python3 manage.py shell -c "from songs.models import GenreTag, MoodTag, OccasionTag; print('genres:', list(GenreTag.objects.values_list('id','name'))); print('moods:', list(MoodTag.objects.values_list('id','name'))); print('occasions:', list(OccasionTag.objects.values_list('id','name')))"
```

### Read (GET)

```bash
curl http://127.0.0.1:8000/api/songs/
curl http://127.0.0.1:8000/api/songs/SONG_ID/
```

### Update (PATCH)

```bash
curl -X PATCH http://127.0.0.1:8000/api/songs/SONG_ID/ \
  -H 'Content-Type: application/json' \
  -d '{"status":"Completed","file_path":"/tmp/song.mp3","duration":120}'
```

### Delete (DELETE)

```bash
curl -X DELETE http://127.0.0.1:8000/api/songs/SONG_ID/
```

## Exercise 4 — Strategy Pattern (Mock vs Suno API)

### Strategy selection

Select the active strategy using an environment variable.

Recommended: set it in `.env` (auto-loaded when you run `manage.py`).

- `GENERATOR_STRATEGY=mock` (default)
- `GENERATOR_STRATEGY=suno`

Important: `GENERATOR_STRATEGY` is read when Django starts (from settings). If you change it, restart `python3 manage.py runserver`.

### Generation endpoints

- `POST /api/songs/<SONG_ID>/generate/` — start generation
- `GET  /api/songs/<SONG_ID>/generate/` — poll/refresh status

### Mock mode (recommended for development)

Set in `.env`:

```env
GENERATOR_STRATEGY=mock
```

Then start the server:

```bash
cd backend && python3 manage.py runserver
```

Start generation:

```bash
curl -X POST http://127.0.0.1:8000/api/songs/SONG_ID/generate/
```

Expected result (example):

- `generation.status` is `SUCCESS`
- `song.file_path` is a predictable mock URL

#### Quick demo (copy/paste): get a real `SONG_ID`, then generate

```bash
# 1) List existing songs (grab any "id")
curl http://127.0.0.1:8000/api/songs/

# 2) If the list is empty, create a song.
#    Create the song (the response includes an "id")
curl -X POST http://127.0.0.1:8000/api/songs/ \
  -H 'Content-Type: application/json' \
  -d '{"title":"Demo Song","prompt_text":"lofi chill beat","voice_type":"female"}'

# 3) Start generation using that returned id
curl -X POST http://127.0.0.1:8000/api/songs/REAL_ID/generate/
```

### Suno mode (SunoApi.org)

Suno API requests use **Bearer token auth** and the following endpoints:

- `POST https://api.sunoapi.org/api/v1/generate`
- `GET  https://api.sunoapi.org/api/v1/generate/record-info?taskId=<TASK_ID>`

#### Configure the API key (do not commit it)

Recommended: use a local `.env` file (kept out of git). Django loads `.env` automatically when you run `manage.py`.

```bash
# edit .env and set at least:
#   GENERATOR_STRATEGY=suno
#   SUNO_API_KEY=YOUR_API_KEY
#
# Some SunoApi.org deployments also require a callback URL. If you get:
#   "Suno API error (code=400): Please enter callBackUrl."
# then:
#   1) Open https://webhook.site and copy your unique URL
#   2) Set it in .env as SUNO_CALLBACK_URL=<that URL>
#      (example format: https://webhook.site/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)

# example:
# GENERATOR_STRATEGY=suno
# SUNO_API_KEY=YOUR_API_KEY
```

Minimal flow (polling):

```bash
cd backend && python3 manage.py runserver

curl -X POST http://127.0.0.1:8000/api/songs/SONG_ID/generate/
curl http://127.0.0.1:8000/api/songs/SONG_ID/generate/
```

When status becomes `SUCCESS`, the API updates `song.file_path` to the returned `audioUrl/audio_url`.

## Demonstration (unit tests)

These tests demonstrate generation in both modes without requiring network access.

```bash
cd backend && python3 manage.py test songs
```

What’s covered:

- Mock generation via the API endpoint (`POST /api/songs/<id>/generate/`)
- Suno strategy request + record-info parsing (HTTP calls are mocked)