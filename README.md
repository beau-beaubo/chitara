# Chitara AI Music Platform - Domain Layer (Exercise 3)

## Project Overview
Chitara is an AI-powered music generation platform. This repository contains the implementation of the **Domain Layer** using Django, focusing on core entities: Users and Songs.

## Domain Architecture
- **Users**: Implements provider-agnostic authentication via `ExternalID`.
- **Songs**: Stores AI-generated tracks with metadata including `prompt_text`, `voice_type`, and `status`.
- **Relationships**: Utilizes Many-to-Many relationships for Genre, Mood, and Occasion to support flexible AI parameters.

## Setup Instructions
1. **Clone the repository**:
   `git clone git@github.com:beau-beaubo/chitara.git`
2. **Create and activate a virtual environment (recommended)**:
   - macOS/Linux:
     - `python3 -m venv .venv`
     - `source .venv/bin/activate`
3. **Install dependencies**:
   - `pip install -r backend/requirements.txt`
4. **Apply migrations**:
   - `cd backend`
   - `python3 manage.py makemigrations`
   - `python3 manage.py migrate`
5. **Create an admin user**:
   - `python3 manage.py createsuperuser`
6. **Run the server**:
   - `python3 manage.py runserver`

## CRUD Demonstration (Task 4)
CRUD is demonstrated via a **simple JSON API** (primary) and Django Admin (secondary).

### Option A — Simple API (recommended)
Base URL: `http://127.0.0.1:8000`

Start the server:
`cd backend && python3 manage.py runserver`

1) Create (POST)
- Create a song (replace `CREATOR_ID` with an existing user id; must be a positive integer like `1`):
   `curl -X POST http://127.0.0.1:8000/api/songs/ -H 'Content-Type: application/json' -d '{"title":"My First Song","creator_id":CREATOR_ID,"prompt_text":"lofi chill beat","voice_type":"female"}'`

Find a valid `CREATOR_ID`:
- Admin: open `http://127.0.0.1:8000/admin/users/user/`
- Or shell:
   `cd backend && python3 manage.py shell -c "from django.contrib.auth import get_user_model; print(list(get_user_model().objects.values_list('id','username')))"`

2) Read (GET)
- List songs:
   `curl http://127.0.0.1:8000/api/songs/`
- Get one song (replace `SONG_ID`):
   `curl http://127.0.0.1:8000/api/songs/SONG_ID/`

3) Update (PATCH)
- Update status/file path:
   `curl -X PATCH http://127.0.0.1:8000/api/songs/SONG_ID/ -H 'Content-Type: application/json' -d '{"status":"Completed","file_path":"/tmp/song.mp3","duration":120}'`

4) Delete (DELETE)
- Delete a song:
   `curl -X DELETE http://127.0.0.1:8000/api/songs/SONG_ID/`

### Option B — Django Admin
1. Open Admin: `http://127.0.0.1:8000/admin/`
2. Log in with your superuser
3. Create/Read/Update/Delete `Song` and the tag entities (`GenreTag`, `MoodTag`, `OccasionTag`)