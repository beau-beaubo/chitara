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
CRUD is demonstrated via **Django Admin**.

1. Start the server: `cd backend && python3 manage.py runserver`
2. Open Admin: `http://127.0.0.1:8000/admin/`
3. Log in with your superuser

Evidence of CRUD (what to do in Admin):
- Create: add `GenreTag`/`MoodTag`/`OccasionTag`, then create a `Song` with those tags
- Read: use the list views + search/filter on the `Song` changelist
- Update: edit a `Song` (e.g., change `status`, `is_shared`, `file_path`, `duration`)
- Delete: delete a `Song` (and confirm it is removed from the list)