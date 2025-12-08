from flask import Flask, request, render_template, redirect, url_for, flash, send_file, session
import os
import tempfile
from werkzeug.utils import secure_filename
from src.processor import procesar_archivos, importar_csv
from src.database.db import Sesion
from src.models import Carrera, Asignatura, Titulo, Adquisicion
from src.database.migrate_db import migrate_db  # Assuming this sets up the DB

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# Initialize DB
migrate_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    download_link = None
    show_options = False
    if request.method == 'POST':
        facultad = request.form['facultad']
        carrera = request.form['carrera']
        files = request.files.getlist('files')
        csv_file = request.files.get('csv_file')

        # Handle CSV import
        if csv_file and csv_file.filename:
            if csv_file.filename.endswith('.csv'):
                csv_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(csv_file.filename))
                csv_file.save(csv_path)
                try:
                    importar_csv(csv_path)
                    flash('¡CSV importado exitosamente!')
                except Exception as e:
                    flash(f'Error al importar CSV: {str(e)}')
                return redirect(url_for('index'))

        # Handle PDF processing
        if not files or all(f.filename == '' for f in files):
            flash('No se subieron archivos PDF')
            return redirect(request.url)

        # Save uploaded files to temp directory
        upload_dir = tempfile.mkdtemp()
        for file in files:
            # Aceptar archivos PDF y Word
            if file and (file.filename.endswith('.pdf') or file.filename.endswith('.docx')):
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_dir, filename))

        # Process the PDFs
        try:
            procesar_archivos(upload_dir, facultad=facultad, carrera_default=carrera)
            flash('¡Procesamiento completado exitosamente!')
            # Check if CSV was generated
            csv_path = 'reporte_bibliografia.csv'
            if os.path.exists(csv_path):
                session['show_options'] = True
                session['download_link'] = url_for('download_csv')
                show_options = True
                download_link = url_for('download_csv')
        except Exception as e:
            flash(f'Error durante el procesamiento: {str(e)}')

        return redirect(url_for('index'))

    # Check session for persistent options
    if session.get('show_options'):
        show_options = True
        download_link = session.get('download_link')
        # Clear session so it doesn't persist on refresh or new visit
        session.pop('show_options', None)
        session.pop('download_link', None)

    return render_template('index.html', download_link=download_link, show_options=show_options)

@app.route('/download_csv')
def download_csv():
    csv_path = 'reporte_bibliografia.csv'
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True, download_name='reporte_bibliografia.csv')
    else:
        flash('No se encontró el archivo CSV')
        return redirect(url_for('index'))

@app.route('/clear_session', methods=['POST'])
def clear_session():
    session.pop('show_options', None)
    session.pop('download_link', None)
    return '', 204

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Usa el puerto que asigna Railway
    app.run(host="0.0.0.0", port=port, debug=False)
