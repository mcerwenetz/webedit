# webedit

A simple Markdown note-taking app built with Flask and served via waitress.

## Requirements

- Python 3.x
- pip

## Setup

1. Clone the repository and navigate into it:

```
git clone https://github.com/mcerwenetz/webedit.git
cd webedit
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Edit `conf.py` and set a secret key and password:

```python
SECRET = 'your-secret-key'
PASSWORD = 'your-password'
```

## Running

```
python app.py
```

The app starts on `http://127.0.0.1:8080/notes`. Open that URL in your browser and log in with the password set in `conf.py`.

## Notes

- The database file `markdown_notes.db` is created automatically on first run in the project directory.
- The `url_scheme='https'` parameter in `app.py` is intended for use behind a reverse proxy. If running locally without a proxy, remove it or the login redirect may not work correctly.
