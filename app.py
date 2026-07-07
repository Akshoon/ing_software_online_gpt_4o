"""
Adaptador primario: Flask Web Application
Recibe solicitudes HTTP y las delega a los casos de uso a través del contenedor.
"""
from flask import Flask, request, render_template, redirect, url_for, flash, send_file, session
import os
import tempfile
from werkzeug.utils import secure_filename

from src.infrastructure.database.migrate_db import migrate_db
from src.infrastructure.database.db import init_db
from src.container import (
    build_process_files_use_case,
    build_generate_report_use_case,
    build_import_csv_use_case,
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# Inicializar DB
init_db()
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
