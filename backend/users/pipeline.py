# users/pipeline.py
def save_external_id(backend, user=None, response=None, *args, **kwargs):
    if backend.name == "google-oauth2" and user:
        # Google uses 'sub' as the unique identifier
        external_id = response.get("sub") or response.get("id")
        if external_id:
            # Check if another user already has this ID to avoid IntegrityError
            user.external_id = external_id
            user.save(update_fields=['external_id'])