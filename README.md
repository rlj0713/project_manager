# project_manager

Minimal Flask application starter.

## Run

```bash
python3 -m pip install -r requirements.txt
python3 backend/app.py
```

Open http://127.0.0.1:5000/ in a browser.

Initialize the development users once:

```bash
cd backend
python3 seed.py
```

Development credentials are `alice` / `alice123` (admin), `bob` / `bob123`
(non-admin), and `carol` / `carol123` (non-admin).
