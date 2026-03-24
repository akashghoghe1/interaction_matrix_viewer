# interaction_matrix_viewer
This tool helps identifying dependencies on different software/hardware module to expediting the issue triaging and stakeholder identification for quicker resolution.

## Deploying on Render

Use a **Python Web Service** with:

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:server --bind 0.0.0.0:$PORT`

Notes:
- The app reads `PORT` automatically in local run mode (`python app.py`) and defaults to `8050`.
- `gunicorn` is included in `requirements.txt` for Render production startup.
