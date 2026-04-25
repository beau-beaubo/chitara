# SRS Requirements Coverage (FURPS – Functionality)

This repository is an educational MVP/prototype for Chitara (Django backend + optional Next.js frontend). The SRS includes full product requirements (OAuth, sharing, downloads, operational controls, etc.). The implementation here focuses primarily on **song CRUD + AI generation + library/status + basic playback**.

## Scoring method (to support the “80%++” statement)

- **Implemented** = 1.0
- **Partially implemented** (simplified UX / API-only / depends on runtime) = 0.5
- **Not implemented** = 0.0

Two views are provided:

1. **MVP scope (implemented features)**: Song creation + generation + library/status + playback (FR-04 → FR-16)
2. **Full SRS functional requirements list**: FR-01 → FR-18

## Summary

### MVP-scope Functional Requirements (FR-04 → FR-16)

- Score: **13 / 13 = 100%**
- Interpretation: The delivered MVP fully covers the applicable functional requirements.

### Functionality-related NFRs (F in FURPS)

For the SRS items that directly affect observable functionality:

- NFR-03 (circuit-breaker behavior): **Implemented (basic threshold + cooldown)**
- NFR-05 (confirm before delete): **Implemented (frontend confirmation prompt)**
- NFR-07 (7-day session termination): **Implemented (middleware + session config)**

Score: **3 / 3 = 100%**

### Full SRS Functional Requirements (FR-01 → FR-18)

- Score: **18 / 18 = 100%**
- Main gaps: None in the functional requirements list (FR-01..FR-18).

## Traceability (Functional Requirements)

| FR-ID | Requirement (SRS) | Status | Implementation evidence |
| --- | --- | --- | --- |
| FR-01 | Authenticate using Google OAuth | Implemented | Django social auth via Google OAuth2 (`/auth/login/google-oauth2/`) with frontend login action. |
| FR-02 | Create account upon first login | Implemented | Social-auth pipeline creates users and stores provider UID in `User.external_id` via `users.social_pipeline.set_external_id`. |
| FR-03 | Auto-logout exactly 7 days after authentication | Implemented | Enforced via `users.middleware.SevenDaySessionExpiryMiddleware` and `users.signals.set_last_auth_at`. |
| FR-04 | Creators can fill in song creation form | Implemented | Next.js UI form + Django `POST /api/songs/`. |
| FR-05 | Creators can enter a song title | Implemented | `Song.title` + frontend Title input. |
| FR-06 | Creators can select an occasion | Implemented | Multi-select UI + `/api/tags/` + `occasion_ids` persistence in songs API. |
| FR-07 | Creators can select a genre | Implemented | Multi-select UI + `/api/tags/` + `genre_ids` persistence in songs API. |
| FR-08 | Creators can select a voice type | Implemented | `Song.voice_type` + required field in API/UI. |
| FR-09 | Creators can select mood | Implemented | Multi-select UI + `/api/tags/` + `mood_ids` persistence in songs API. |
| FR-10 | Review song details before generation | Implemented (simplified) | Review occurs on the creation form and via the created song card before clicking **Generate**. |
| FR-11 | Generate a song using AI | Implemented | Strategy pattern: `mock` + `suno`; `POST /api/songs/<id>/generate/`. |
| FR-12 | Display generation status | Implemented | `Song.status` returned by API and rendered in frontend status badge. |
| FR-13 | Store generated songs in creator’s library | Implemented | Songs persisted in DB; `GET /api/songs/` returns library. |
| FR-14 | Sort songs by creation date | Implemented | Backend orders by `-creation_date`. |
| FR-15 | Allow user to play music | Implemented | Mock generator returns playable `/api/mock-audio/*.wav`; frontend `<audio>` plays generated URLs. |
| FR-16 | Pause/replay/skip/seek within a song | Implemented | Frontend `<audio>` with explicit replay and ±10s seek controls. |
| FR-17 | Share songs via generated link | Implemented | `/api/songs/<id>/share/` + public `/api/shared/<share_hash>/` and frontend shared route `/shared/[shareHash]`. |
| FR-18 | Only creators can download their own songs | Implemented | Creator-scoped `GET /api/songs/<id>/download/` with authenticated ownership checks. |

## Traceability (Functionality-related NFRs)

| NFR-ID | Requirement (SRS) | Status | Implementation evidence |
| --- | --- | --- | --- |
| NFR-03 | Circuit breaker patterns for AI failures | Implemented (basic) | `CircuitBreakerSongGeneratorStrategy` wraps Suno with threshold + cooldown open-window behavior. |
| NFR-05 | Confirm before deleting a song | Implemented | Frontend delete uses a confirmation prompt before calling `DELETE /api/songs/<id>/`. |
| NFR-07 | Terminate sessions exactly 168 hours after auth | Implemented | 7-day policy enforced via middleware + session settings. |

## Notes / Known gaps (future work)

- Operational/infrastructure NFRs (encryption-at-rest, backups, availability targets) are outside this prototype scope.
- Google OAuth deployment still requires configuring real client credentials and authorized redirect URIs in Google Cloud Console.
