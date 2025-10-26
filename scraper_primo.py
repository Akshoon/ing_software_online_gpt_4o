from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import time

# Función para buscar y extraer información de libros en Primo
def buscar_libro_detalles(termino_busqueda, verbose=False):
    """
    Busca un libro en el catálogo Primo de la UAH y extrae sus detalles.
    
    Args:
        termino_busqueda (str): Término de búsqueda (título o autor)
        verbose (bool): Si es True, imprime mensajes de depuración
    
    Returns:
        dict: Diccionario con los detalles del libro o None si hay error
              {
                  'titulo': str,
                  'autor': str,
                  'editor': str,
                  'fecha_creacion': str,
                  'edicion': str,
                  'formato': str,
                  'disponibilidad_fisica': str,
                  'disponibilidad_online': str
              }
    """
    # Codifica el término de búsqueda para la URL
    termino_codificado = urllib.parse.quote(termino_busqueda)

    # Configura el navegador en modo headless (sin interfaz gráfica)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # Inicializa el navegador con las opciones
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    except Exception as e:
        if verbose:
            print(f"Error al inicializar el navegador: {e}")
        return None

    # Construye la URL de búsqueda con el término codificado
    url = f'https://uahurtado.primo.exlibrisgroup.com/discovery/search?query=any,contains,{termino_codificado}&tab=Everything&search_scope=MyInst_and_CI&vid=56UAH_INST:56UAH_INST&offset=0'
    
    try:
        driver.get(url)
        
        # Pequeña pausa para que la página cargue
        time.sleep(2)
        
        # Espera hasta que los resultados de búsqueda estén visibles
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.list-item-wrapper'))
        )
    except Exception as e:
        # No se encontraron resultados
        if verbose:
            print(f"No se encontraron resultados de búsqueda para: {termino_busqueda}")
        driver.quit()
        return None

    # Encuentra el primer resultado de búsqueda
    try:
        # Intenta encontrar el enlace del título dentro del primer resultado
        primer_resultado = driver.find_element(By.CSS_SELECTOR, '.list-item-wrapper')
        
        # Busca el enlace del título dentro del primer resultado
        # Intenta varios selectores posibles
        libro_enlace = None
        libro_url = None
        selectores_posibles = [
            '.item-title a',  # Enlace dentro del título del item
            'a[href*="fulldisplay"]',  # Enlaces que contienen "fulldisplay" en la URL
            'prm-search-result-list-item a',  # Enlaces dentro del componente de resultado
            'a.md-primoExplore-theme',  # Selector original como fallback
        ]
        
        for selector in selectores_posibles:
            try:
                libro_enlace = primer_resultado.find_element(By.CSS_SELECTOR, selector)
                if libro_enlace:
                    libro_url = libro_enlace.get_attribute('href')
                    if libro_url and libro_url.strip():  # Verifica que la URL no esté vacía
                        if verbose:
                            print(f"✓ Enlace encontrado con selector: {selector}")
                        break
            except:
                continue
        
        if not libro_enlace or not libro_url or not libro_url.strip():
            if verbose:
                print("✗ Error: No se pudo encontrar un enlace válido al libro")
                print("Intentando hacer clic directamente en el primer resultado...")
            # Como último recurso, intenta hacer clic en el primer resultado
            libro_enlace = primer_resultado.find_element(By.CSS_SELECTOR, '.item-title a')
            libro_enlace.click()
            
            # Espera a que cambie la URL (navegación completada)
            WebDriverWait(driver, 20).until(
                lambda d: 'fulldisplay' in d.current_url or 'discovery/fulldisplay' in d.current_url
            )
            if verbose:
                print(f"✓ Navegación completada. URL actual: {driver.current_url}")
        else:
            # Reemplaza "&amp;" por "&" para asegurar que la URL esté bien formada
            libro_url = libro_url.replace("&amp;", "&")
            if verbose:
                print(f"Accediendo al libro con URL: {libro_url}")
            
            # Abre la página del libro usando la URL extraída
            driver.get(libro_url)
            
    except Exception as e:
        if verbose:
            print(f"✗ Error al extraer el enlace del libro: {e}")
            print("Intentando estrategia alternativa...")
        # Estrategia alternativa: hacer clic directamente
        try:
            primer_resultado = driver.find_element(By.CSS_SELECTOR, '.list-item-wrapper .item-title a')
            primer_resultado.click()
            # Espera a que cambie la URL
            WebDriverWait(driver, 20).until(
                lambda d: 'fulldisplay' in d.current_url
            )
            if verbose:
                print(f"✓ Navegación completada mediante clic. URL actual: {driver.current_url}")
        except Exception as e2:
            if verbose:
                print(f"✗ Error en estrategia alternativa: {e2}")
            driver.quit()
            return None

    # Espera hasta que la página del libro esté completamente cargada
    # Intenta varios selectores para el título
    title_selectors = [
        'span[ng-bind-html*="highlightedText"]',  # Selector específico para el título con Angular
        'h1.item-title',
        'h1',
        '.full-view-section-title',
        'prm-full-view-service-container h1'
    ]
    
    title_element = None
    for selector in title_selectors:
        try:
            title_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            if title_element:
                if verbose:
                    print(f"✓ Título encontrado con selector: {selector}")
                break
        except:
            continue
    
    if not title_element:
        if verbose:
            print("✗ No se pudo encontrar el título del libro")
        driver.quit()
        return None

    # Intentar extraer los detalles del libro
    try:
        if verbose:
            print(f"\n{'='*60}")
            print(f"DETALLES DEL LIBRO")
            print(f"{'='*60}")
        
        # Diccionario para almacenar los detalles
        detalles = {
            'titulo': None,
            'autor': None,
            'editor': None,
            'fecha_creacion': None,
            'edicion': None,
            'formato': None,
            'disponibilidad_fisica': None,
            'disponibilidad_online': None
        }
        
        # Extraer título
        try:
            detalles['titulo'] = driver.find_element(By.CSS_SELECTOR, 'span[ng-bind-html*="highlightedText"]').text
        except:
            try:
                detalles['titulo'] = driver.find_element(By.CSS_SELECTOR, 'h1').text
            except:
                detalles['titulo'] = title_element.text if title_element else None
        
        if verbose:
            print(f"Título: {detalles['titulo'] if detalles['titulo'] else 'No disponible'}")
        
        # Extraer todos los detalles usando la estructura de la página
        # Buscar todos los divs con detalles - intentar múltiples selectores
        detail_sections = []
        
        # Intentar diferentes selectores para encontrar las secciones de detalles
        selectors_to_try = [
            '.spaced-rows > div[layout="row"]',
            '.spaced-rows div[layout="row"]',
            'div[layout="row"][ng-if="$ctrl.showDetail(detail)"]',
            '.item-details-section div[layout="row"]'
        ]
        
        for selector in selectors_to_try:
            detail_sections = driver.find_elements(By.CSS_SELECTOR, selector)
            if detail_sections:
                if verbose:
                    print(f"✓ Encontradas {len(detail_sections)} secciones de detalles con selector: {selector}")
                break
        
        # Mapeo de nombres de campos a claves del diccionario
        campo_map = {
            'Autor': 'autor',
            'Editor': 'editor',
            'Fecha de creación': 'fecha_creacion',
            'Edición': 'edicion',
            'Formato': 'formato'
        }
        
        if not detail_sections:
            if verbose:
                print("✗ No se encontraron secciones de detalles. Intentando método alternativo...")
            # Método alternativo: buscar directamente los labels
            try:
                labels = driver.find_elements(By.CSS_SELECTOR, 'span.bold-text[data-details-label]')
                if verbose:
                    print(f"✓ Encontrados {len(labels)} campos mediante labels")
                for label_elem in labels:
                    try:
                        label = label_elem.text.strip()
                        if label == "Título":
                            continue
                        
                        # Buscar el contenedor padre y luego el valor
                        parent = label_elem.find_element(By.XPATH, './ancestor::div[@layout="row"]')
                        value_container = parent.find_element(By.CSS_SELECTOR, '.item-details-element-container')
                        
                        # Intentar extraer el valor
                        value_spans = value_container.find_elements(By.CSS_SELECTOR, 'span[ng-bind-html]')
                        if value_spans:
                            value = value_spans[0].text.strip()
                            if value and label in campo_map:
                                detalles[campo_map[label]] = value
                                if verbose:
                                    print(f"{label}: {value}")
                        else:
                            value = value_container.text.strip()
                            lines = [line.strip() for line in value.split('\n') if line.strip()]
                            filtered = [line for line in lines if line.lower() not in ['more', 'hide', 'mostrar todo', 'mostrar menos']]
                            if filtered and label in campo_map:
                                detalles[campo_map[label]] = filtered[0]
                                if verbose:
                                    print(f"{label}: {filtered[0]}")
                    except Exception as e:
                        continue
            except Exception as e:
                if verbose:
                    print(f"✗ Error en método alternativo: {e}")
        
        # Procesar solo hasta el campo "Formato" (5 campos después del título)
        campos_procesados = 0
        for idx, section in enumerate(detail_sections):
            try:
                # Obtener el label (título del campo)
                label_elem = section.find_element(By.CSS_SELECTOR, 'span.bold-text')
                label = label_elem.text.strip()
                
                # Saltar si es el título (ya lo imprimimos arriba)
                if label == "Título":
                    continue
                
                # Detener después del campo "Formato"
                if campos_procesados >= 5:
                    break
                
                # Obtener el valor del campo
                value = None
                
                # Buscar span con ng-bind-html
                try:
                    value_elems = section.find_elements(By.CSS_SELECTOR, '.item-details-element-container span[ng-bind-html]')
                    if value_elems:
                        # Tomar el primer elemento visible
                        for elem in value_elems:
                            if elem.is_displayed() and elem.text.strip():
                                value = elem.text.strip()
                                break
                except:
                    pass
                
                # Guardar el valor en el diccionario
                if label in campo_map:
                    detalles[campo_map[label]] = value if value and value != label else None
                    if verbose:
                        if value and value != label:
                            print(f"{label}: {value}")
                        else:
                            print(f"{label}: No disponible")
                    campos_procesados += 1
                    
            except Exception as e:
                continue
        
        # Buscar información de disponibilidad física
        try:
            disponibilidad_elem = driver.find_element(By.CSS_SELECTOR, 'p[ng-if="$ctrl.currLoc.location.availabilityStatement"]')
            detalles['disponibilidad_fisica'] = disponibilidad_elem.text.strip()
            if verbose:
                print(f"Disponibilidad física: {detalles['disponibilidad_fisica']}")
        except:
            detalles['disponibilidad_fisica'] = None
            if verbose:
                print("Disponibilidad física: No disponible")

        # Buscar información de disponibilidad online - basándose únicamente en el elemento específico
        detalles['disponibilidad_online'] = None

        # Buscar el elemento con clase "availability-status" y verificar si dice "Disponible en línea"
        try:
            availability_elem = driver.find_element(By.CSS_SELECTOR, '.availability-status')
            availability_text = availability_elem.text.strip()
            if availability_text == "Disponible en línea":
                detalles['disponibilidad_online'] = "Disponible en línea"
                if verbose:
                    print(f"Disponibilidad online: {detalles['disponibilidad_online']}")
            else:
                detalles['disponibilidad_online'] = None
                if verbose:
                    print(f"Disponibilidad online: {availability_text} (no es 'Disponible en línea')")
        except:
            detalles['disponibilidad_online'] = None
            if verbose:
                print("Disponibilidad online: Elemento no encontrado")
        
        if verbose:
            print(f"{'='*60}\n")
        
        # Cerrar el navegador
        driver.quit()
        
        return detalles
    
    except Exception as e:
        if verbose:
            print(f"✗ Error al extraer los detalles del libro: {e}")
            import traceback
            traceback.print_exc()
        
        # Cerrar el navegador en caso de error
        driver.quit()
        return None

# Ejemplo de uso
if __name__ == '__main__':
    # Llamada a la función con un término de búsqueda
    resultado = buscar_libro_detalles("La interpretacion de las culturas", verbose=True)
    if resultado:
        print("\nResultado final:")
        for campo, valor in resultado.items():
            print(f"  {campo}: {valor}")
