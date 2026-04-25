# Chitara (Django backend) — Exercises 3

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