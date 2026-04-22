# Chitara (Django backend) — Exercises 3 & 4

Chitara is an AI-powered music generation platform. This repo contains the Django backend/domain layer for **Users** and **Songs**, plus Exercise 4’s Strategy-based song generation (Mock vs Suno).

## What’s implemented
- Users: custom `User` model with `external_id`
- Songs: `Song` model + tags (`GenreTag`, `MoodTag`, `OccasionTag`)
- Simple JSON API (no frontend/UI required for these exercises)
- Song generation strategies:
  - `mock` (offline, deterministic)
  - `suno` (calls SunoApi.org using Bearer token)

## Quickstart

```bash
git clone git@github.com:beau-beaubo/chitara.git
cd chitara

python3 -m venv .venv
source .venv/bin/activate

pip install -r backend/requirements.txt

cd backend
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

Base URL: `http://127.0.0.1:8000`

## Placeholders used below

- `CREATOR_ID`: numeric user id (the `Song.creator`)
- `SONG_ID`: numeric song id

If you see a 404 like **“No Song matches the given query.”**, it means that `SONG_ID` does not exist in your database.

## Exercise 3 — Songs CRUD (JSON API)

### Find a valid `CREATOR_ID`

- Admin: `http://127.0.0.1:8000/admin/users/user/`
- Or shell:

```bash
cd backend
python3 manage.py shell -c "from django.contrib.auth import get_user_model; print(list(get_user_model().objects.values_list('id','username')))"
```

### Create (POST)

```bash
curl -X POST http://127.0.0.1:8000/api/songs/ \
  -H 'Content-Type: application/json' \
  -d '{"title":"My First Song","creator_id":CREATOR_ID,"prompt_text":"lofi chill beat","voice_type":"female"}'
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

Select the active strategy using an environment variable:

- `GENERATOR_STRATEGY=mock` (default)
- `GENERATOR_STRATEGY=suno`

### Generation endpoints

- `POST /api/songs/<SONG_ID>/generate/` — start generation
- `GET  /api/songs/<SONG_ID>/generate/` — poll/refresh status

### Mock mode (recommended for development)

```bash
export GENERATOR_STRATEGY=mock
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
#    First, find a valid CREATOR_ID (needs at least one user/superuser)
cd backend && python3 manage.py shell -c "from django.contrib.auth import get_user_model; print(list(get_user_model().objects.values_list('id','username')))"

#    Create the song (the response includes an "id")
curl -X POST http://127.0.0.1:8000/api/songs/ \
  -H 'Content-Type: application/json' \
  -d '{"title":"Demo Song","creator_id":CREATOR_ID,"prompt_text":"lofi chill beat","voice_type":"female"}'

# 3) Start generation using that returned id
curl -X POST http://127.0.0.1:8000/api/songs/REAL_ID/generate/
```

### Suno mode (SunoApi.org)

Suno API requests use **Bearer token auth** and the following endpoints:

- `POST https://api.sunoapi.org/api/v1/generate`
- `GET  https://api.sunoapi.org/api/v1/generate/record-info?taskId=<TASK_ID>`

#### Configure the API key (do not commit it)

Recommended: use a local `.env` file (kept out of git).

```bash
cp .env.example .env

# edit .env and set at least:
#   GENERATOR_STRATEGY=suno
#   SUNO_API_KEY=YOUR_API_KEY

set -a && source .env && set +a
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