import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import threading
from main import procesar_pdfs, generar_reportes
from models import Sesion, Carrera

class BibliografiaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesador de Bibliografía - UAH")
        self.root.geometry("600x500")

        # Variables
        self.facultad_var = tk.StringVar(value="Ciencias Sociales")
        self.carrera_var = tk.StringVar(value="Trabajo Social")
        self.pdf_dir_var = tk.StringVar(value="archivos/")

        # Crear widgets
        self.create_widgets()

        # Cargar carreras existentes
        self.load_existing_careers()

    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Título
        title_label = ttk.Label(main_frame, text="Procesador de Bibliografía Académica",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Facultad
        ttk.Label(main_frame, text="Facultad:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.facultad_entry = ttk.Entry(main_frame, textvariable=self.facultad_var, width=40)
        self.facultad_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        # Carrera
        ttk.Label(main_frame, text="Carrera:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.carrera_combo = ttk.Combobox(main_frame, textvariable=self.carrera_var, width=37)
        self.carrera_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        self.carrera_combo['values'] = ["Trabajo Social"]  # Default

        # Directorio PDFs
        ttk.Label(main_frame, text="Directorio PDFs:").grid(row=3, column=0, sticky=tk.W, pady=5)
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.pdf_dir_var, width=30)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.browse_button = ttk.Button(dir_frame, text="Examinar", command=self.browse_directory)
        self.browse_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        self.process_button = ttk.Button(button_frame, text="Procesar PDFs",
                                       command=self.process_pdfs, width=20)
        self.process_button.pack(side=tk.LEFT, padx=(0, 10))

        self.report_button = ttk.Button(button_frame, text="Generar Reporte",
                                      command=self.generate_report, width=20)
        self.report_button.pack(side=tk.LEFT)

        # Área de estado
        ttk.Label(main_frame, text="Estado:").grid(row=5, column=0, sticky=tk.W, pady=(20, 5))
        self.status_text = tk.Text(main_frame, height=10, width=60, state=tk.DISABLED)
        self.status_text.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbar para el área de estado
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=6, column=2, sticky=(tk.N, tk.S))
        self.status_text['yscrollcommand'] = scrollbar.set

        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)

    def load_existing_careers(self):
        """Carga las carreras existentes de la base de datos."""
        try:
            sesion = Sesion()
            carreras = sesion.query(Carrera).all()
            career_names = [c.name for c in carreras]
            if not career_names:
                career_names = ["Trabajo Social"]
            self.carrera_combo['values'] = career_names
            sesion.close()
        except Exception as e:
            self.log_message(f"Error cargando carreras: {str(e)}")

    def browse_directory(self):
        """Abre diálogo para seleccionar directorio."""
        directory = filedialog.askdirectory()
        if directory:
            self.pdf_dir_var.set(directory)

    def process_pdfs(self):
        """Procesa los PDFs con los parámetros especificados."""
        facultad = self.facultad_var.get().strip()
        carrera = self.carrera_var.get().strip()
        pdf_dir = self.pdf_dir_var.get().strip()

        if not facultad or not carrera:
            messagebox.showerror("Error", "Por favor, ingrese facultad y carrera.")
            return

        if not os.path.exists(pdf_dir):
            messagebox.showerror("Error", f"El directorio '{pdf_dir}' no existe.")
            return

        # Deshabilitar botones durante procesamiento
        self.process_button.config(state=tk.DISABLED)
        self.report_button.config(state=tk.DISABLED)

        self.log_message(f"Iniciando procesamiento...\nFacultad: {facultad}\nCarrera: {carrera}\nDirectorio: {pdf_dir}\n")

        # Ejecutar en un hilo separado para no bloquear la GUI
        def run_processing():
            try:
                # Redirigir stdout para capturar logs
                import io
                from contextlib import redirect_stdout

                f = io.StringIO()
                with redirect_stdout(f):
                    procesar_pdfs(pdf_dir, facultad, carrera)

                output = f.getvalue()
                # Usar after para actualizar la UI en el hilo principal
                self.root.after(0, lambda: self.log_message(output))
                self.root.after(0, lambda: messagebox.showinfo("Éxito", "Procesamiento completado."))

            except Exception as e:
                error_msg = f"Error durante el procesamiento: {str(e)}"
                self.root.after(0, lambda: self.log_message(error_msg))
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

            finally:
                # Rehabilitar botones
                self.root.after(0, lambda: self.process_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.report_button.config(state=tk.NORMAL))

        thread = threading.Thread(target=run_processing)
        thread.start()

    def generate_report(self):
        """Genera el reporte CSV."""
        self.log_message("Generando reporte...\n")

        # Deshabilitar botones durante generación
        self.process_button.config(state=tk.DISABLED)
        self.report_button.config(state=tk.DISABLED)

        # Ejecutar en un hilo separado para no bloquear la GUI
        def run_report():
            try:
                # Redirigir stdout
                import io
                from contextlib import redirect_stdout

                f = io.StringIO()
                with redirect_stdout(f):
                    generar_reportes()

                output = f.getvalue()
                self.root.after(0, lambda: self.log_message(output))
                self.root.after(0, lambda: messagebox.showinfo("Éxito", "Reporte generado exitosamente."))

            except Exception as e:
                error_msg = f"Error generando reporte: {str(e)}"
                self.root.after(0, lambda: self.log_message(error_msg))
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

            finally:
                # Rehabilitar botones
                self.root.after(0, lambda: self.process_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.report_button.config(state=tk.NORMAL))

        thread = threading.Thread(target=run_report)
        thread.start()

    def log_message(self, message):
        """Agrega mensaje al área de estado."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message)
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = BibliografiaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
