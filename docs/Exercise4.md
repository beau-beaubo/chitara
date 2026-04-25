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