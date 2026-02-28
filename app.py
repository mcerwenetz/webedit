from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import markdown
from datetime import datetime
import uuid
from werkzeug.middleware.proxy_fix import ProxyFix
from waitress import serve

app = Flask(__name__)

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

def date_adapter(object_date: datetime) -> str:
    'receives an object_date in the date adapter for adaptation to the new pattern of sqlite3'
    return str(object_date)


def date_converter(val) -> str:
    'receives an object_date in the date adapter for adaptation to the new pattern of sqlite3'
    return datetime.fromisoformat(val.decode())

# Datenbankverbindung
def get_db_connection():
    sqlite3.register_adapter(datetime, date_adapter)
    sqlite3.register_converter("datetime", date_converter)
    conn = sqlite3.connect('markdown_notes.db', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn



# Datenbank initialisieren
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY ,
            title TEXT,
            content TEXT,
            created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Homepage - Liste aller Notizen
@app.route('/')
def index():
    conn = get_db_connection()
    notes = conn.execute('SELECT * FROM notes ORDER BY updated DESC').fetchall()
    conn.close()
    return render_template('index.html', notes=notes)

# Neue Notiz erstellen
@app.route('/create', methods=['GET', 'POST'])
def create():
    conn = get_db_connection()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        md_id = request.form['id']
        
        result = conn.execute('SELECT id from notes where id = ?', (md_id,)).fetchone()
        
        if result:
        
            conn.execute('UPDATE notes SET title = ?, content = ? WHERE id = ?',
+                        (title, content, md_id,))
            conn.commit()
            conn.close()
            
        
        return redirect(url_for('index'))
    elif request.method == 'GET':
        md_id = str(uuid.uuid4())
        conn.execute('INSERT INTO notes (id) VALUES (?)',
                     (md_id,))
        conn.commit()
        conn.close()
        
        return render_template('editor.html', note=None, id=md_id)
    

# Notiz bearbeiten
@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit(md_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        now = datetime.now()
        conn.execute('UPDATE notes SET title = ?, content = ?, updated = ? WHERE id = ?',
                     (title, content, now, md_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    note = conn.execute('SELECT * FROM notes WHERE id = ?', (md_id,)).fetchone()
    conn.close()
    return render_template('editor.html', note=note)

# Notiz als HTML anzeigen
@app.route('/view/<id>')
def view(id):
    conn = get_db_connection()
    note = conn.execute('SELECT * FROM notes WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if note and note['content']:
        html_content = markdown.markdown(note['content'], extensions=['fenced_code', 'tables', 'nl2br'])
        return render_template('view.html', note=note, html_content=html_content)
    return redirect(url_for('index'))

# Notiz löschen
@app.route('/delete/<id>')
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM notes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    conn = get_db_connection()
    search_notes = ""
    
    if query:
        # Alle Notizen laden (für kleine DBs effizient)
        notes = conn.execute('SELECT * FROM notes ORDER BY updated DESC').fetchall()
        conn.close()
        
        notes_content =  [(n['id'], f"{n['title']} {n['content']}") for n in notes]
        scored_notes = [n[0] for n in notes_content if query in n[1]]
        
    
        conn = get_db_connection()
        search_notes = conn.execute(
            'SELECT * FROM notes WHERE id IN (?) ORDER BY updated DESC', (scored_notes)).fetchall()
        conn.close()
        
    
    return render_template('search.html', notes=search_notes, query=query)
    
    # return redirect(url_for('index'))


# API für Auto-Save
@app.route('/autosave/', methods=['POST'])
def autosave():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    id = data.get('id')
    
    now = datetime.now()
    conn = get_db_connection()
    conn.execute('UPDATE notes SET title = ?, content = ?, updated = ? WHERE id = ?',
                 (title, content, now , id))
    conn.commit()
    conn.close()
    
    # JSON-Bestätigung zurückgeben
    return {'status': 'success', 'time': datetime.now().strftime('%H:%M:%S')}



if __name__ == '__main__':
    init_db()
    serve(app, host='127.0.0.1', port=8080, url_prefix='/notes', url_scheme='https')
