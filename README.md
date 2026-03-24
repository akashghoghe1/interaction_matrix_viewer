# interaction_matrix_viewer
This tool helps identifying dependencies on different software/hardware module to expediting the issue triaging and stakeholder identification for quicker resolution.

## Deploying on Render

Use a **Python Web Service** with:

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:server --bind 0.0.0.0:$PORT`

Notes:
- The app reads `PORT` automatically in local run mode (`python app.py`) and defaults to `8050`.
- `gunicorn` is included in `requirements.txt` for Render production startup.
- If Render shows a Python syntax error that references `diff/index` text, trigger a **Clear build cache & deploy**
  so the service uses the latest clean source snapshot.

## Personal profile section setup

To show your own headshot in the "Created & owned by" section, add your image file at:

- `assets/profile.jpg`
- or `assets/profile.jpeg`
- or `assets/profile.png`

The app auto-detects these filenames and uses the first one it finds.
