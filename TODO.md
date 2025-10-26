# TODO List for GUI Implementation

- [x] Modify models.py: Add 'facultad' field to Carrera model
- [x] Update main.py: Modify procesar_pdfs and almacenar_bibliografia to accept facultad and carrera as parameters, use as defaults if extraction fails
- [x] Create gui.py: Implement Tkinter GUI with fields for facultad, carrera (input/select), PDF directory selection, process button, generate report button
- [x] Test the GUI by running it

# TODO List for Web Interface Enhancements

- [x] Add CSV import functionality to main.py (importar_csv function)
- [x] Update app.py to handle CSV uploads and provide download link for generated CSV
- [x] Modify templates/index.html to include CSV upload form and download link
- [x] Test the web interface with CSV import and download
