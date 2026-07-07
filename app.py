"""
Adaptador primario: Flask Web Application
Recibe solicitudes HTTP y las delega a los casos de uso a través del contenedor.
"""
from flask import (
    Flask, request, render_template, redirect, url_for,
    flash, send_file, session, jsonify
)
import os
import tempfile
import functools
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

from src.infrastructure.database.migrate_db import migrate_db
from src.infrastructure.database.db import init_db
from src.container import (
    build_process_files_use_case,
    build_generate_report_use_case,
    build_import_csv_use_case,
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me-in-production-please')
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# Credenciales de acceso (configura en .env)
APP_USER     = os.environ.get('APP_USER', 'admin')
APP_PASSWORD = os.environ.get('APP_PASSWORD', 'admin1234')

# Inicializar DB
init_db()
migrate_db()


# ── Auth helper ───────────────────────────────────────────────
def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated


# ── Login / Logout ────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if username == APP_USER and password == APP_PASSWORD:
            session.permanent = True
            session['logged_in'] = True
            session['username'] = username
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        error = 'Usuario o contraseña incorrectos.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    download_link = None
    show_options = False

    if request.method == 'POST':
        facultad = request.form['facultad']
        carrera = request.form['carrera']
        files = request.files.getlist('files')
        csv_file = request.files.get('csv_file')

        # Manejo de importación CSV
        if csv_file and csv_file.filename:
            if csv_file.filename.endswith('.csv'):
                csv_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(csv_file.filename))
                csv_file.save(csv_path)
                try:
                    use_case = build_import_csv_use_case()
                    use_case.execute(csv_path)
                    flash('¡CSV importado exitosamente!')
                except Exception as e:
                    flash(f'Error al importar CSV: {str(e)}')
                return redirect(url_for('index'))

        # Manejo de procesamiento de archivos PDF/Word
        if not files or all(f.filename == '' for f in files):
            flash('No se subieron archivos PDF')
            return redirect(request.url)

        upload_dir = tempfile.mkdtemp()
        for file in files:
            if file and (file.filename.endswith('.pdf') or file.filename.endswith('.docx')):
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_dir, filename))

        try:
            process_use_case = build_process_files_use_case()
            process_use_case.execute(upload_dir, facultad=facultad, carrera_default=carrera)

            report_use_case = build_generate_report_use_case()
            csv_path = report_use_case.execute()

            flash('¡Procesamiento completado exitosamente!')
            if csv_path and os.path.exists(csv_path):
                session['show_options'] = True
                session['download_link'] = url_for('download_csv')
                show_options = True
                download_link = url_for('download_csv')
        except Exception as e:
            flash(f'Error durante el procesamiento: {str(e)}')

        return redirect(url_for('index'))

    # Verificar sesión para opciones persistentes
    if session.get('show_options'):
        show_options = True
        download_link = session.get('download_link')
        session.pop('show_options', None)
        session.pop('download_link', None)

    return render_template('index.html', download_link=download_link, show_options=show_options)


@app.route('/download_csv')
@login_required
def download_csv():
    csv_path = 'reporte_bibliografia.csv'
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True, download_name='reporte_bibliografia.csv')
    else:
        flash('No se encontró el archivo CSV')
        return redirect(url_for('index'))


@app.route('/clear_session', methods=['POST'])
@login_required
def clear_session():
    session.pop('show_options', None)
    session.pop('download_link', None)
    return '', 204


@app.route('/reporte')
@login_required
def reporte():
    """Página dedicada para visualizar el reporte CSV."""
    return render_template('reporte.html')


@app.route('/api/csv')
@login_required
def api_csv():
    """Retorna el contenido del reporte CSV como JSON para visualización en el frontend."""
    import csv as csv_module
    from flask import jsonify
    csv_path = 'reporte_bibliografia.csv'
    if not os.path.exists(csv_path):
        return jsonify({'exists': False, 'rows': [], 'headers': []})
    rows = []
    headers = []
    try:
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            # Detectar delimitador automáticamente (coma, punto y coma, tabulador, etc.)
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv_module.Sniffer().sniff(sample, delimiters=';,\t|')
            except csv_module.Error:
                dialect = csv_module.excel  # fallback: coma
            reader = csv_module.DictReader(f, dialect=dialect)
            # Sanear cabeceras: None → string vacío y quitar espacios sobrantes
            raw_headers = list(reader.fieldnames or [])
            headers = [(h.strip() if h is not None else '') for h in raw_headers]
            for i, row in enumerate(reader):
                if i >= 500:
                    break
                # Sanear valores y claves: None → ''
                clean_row = {
                    (k.strip() if k is not None else ''): (v.strip() if v is not None else '')
                    for k, v in row.items()
                }
                rows.append(clean_row)
    except Exception as e:
        return jsonify({'exists': True, 'error': str(e), 'rows': [], 'headers': []})
    return jsonify({'exists': True, 'headers': headers, 'rows': rows})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
