# project_manager

Minimal Flask application starter.

## Run

```bash
python3 -m pip install -r requirements.txt
python3 backend/app.py
```

Open http://127.0.0.1:5000/ in a browser. Signed-out visitors are sent to the
login screen automatically. After signing in, the home page is intentionally
blank until project functionality is added.

New users can register at http://127.0.0.1:5000/register. Public registration
always creates a regular, non-admin user.

Initialize the development users once:

```bash
cd backend
python3 seed.py
```

Development credentials are `alice` / `alice123` (admin), `bob` / `bob123`
(non-admin), and `carol` / `carol123` (non-admin).

After signing in as Alice, open http://127.0.0.1:5000/admin to manage regular
users. The admin API supports listing, creating, updating, and deleting
non-admin users. Admin accounts cannot be managed through this page.
