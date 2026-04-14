"""
Servicio para conversion de presentaciones PPTX a imágenes PNG
Proceso: PPTX -> PDF -> PNG usando LibreOffice y pdf2image
"""
import os
import gc  # Garbage collector para liberar memoria
import subprocess
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
from app.database import get_db
from app.models.class_model import Class


# Usar ruta absoluta basada en el directorio de la aplicación
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # /app
PRESENTATIONS_FOLDER = BASE_DIR / 'static' / 'presentations'


class PresentationConverter:
    """Conversor de presentaciones PPTX a imágenes"""

    def __init__(self, presentations_folder=PRESENTATIONS_FOLDER):
        self.presentations_folder = Path(presentations_folder)
        self.presentations_folder.mkdir(parents=True, exist_ok=True)

    def convert_presentation(self, class_id: int, pptx_path: str):
        """
        Convierte un archivo PPTX a imágenes PNG

        Args:
            class_id: ID de la clase
            pptx_path: Ruta al archivo PPTX

        Returns:
            dict con resultado de la conversión
        """
        try:
            pptx_path = Path(pptx_path)
            
            # Si la ruta es relativa, hacerla absoluta desde BASE_DIR
            if not pptx_path.is_absolute():
                pptx_path = BASE_DIR / pptx_path

            # Crear directorio para esta presentación
            presentation_dir = self.presentations_folder / str(class_id)
            presentation_dir.mkdir(parents=True, exist_ok=True)

            # Paso 1: Convertir PPTX a PDF
            pdf_path = presentation_dir / 'temp.pdf'
            success = self._convert_pptx_to_pdf(pptx_path, pdf_path)

            if not success:
                return {
                    'success': False,
                    'error': 'Error convirtiendo PPTX a PDF. Verifica que LibreOffice esté instalado.'
                }

            # Paso 2: Convertir PDF a imágenes
            slide_urls = self._convert_pdf_to_images(pdf_path, presentation_dir, class_id)

            # Paso 3: Limpiar archivo PDF temporal
            if pdf_path.exists():
                pdf_path.unlink()

            # Paso 4: Actualizar clase en BD
            db = next(get_db())
            try:
                class_obj = db.query(Class).filter(Class.id == class_id).first()
                if class_obj:
                    class_obj.slides_count = len(slide_urls)
                    class_obj.slide_urls = slide_urls
                    db.commit()
            finally:
                db.close()

            return {
                'success': True,
                'total_slides': len(slide_urls),
                'slide_urls': slide_urls
            }

        except Exception as e:
            print(f"Error en conversión: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Error en conversión: {str(e)}'
            }

    def _convert_pptx_to_pdf(self, pptx_path: Path, pdf_path: Path) -> bool:
        """Convierte PPTX a PDF usando LibreOffice"""
        try:
            output_dir = pdf_path.parent

            # Ejecutar LibreOffice en modo headless
            result = subprocess.run([
                'soffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', str(output_dir),
                str(pptx_path)
            ], capture_output=True, timeout=120)

            # LibreOffice genera el PDF con el nombre base del archivo PPTX
            generated_pdf = output_dir / f"{pptx_path.stem}.pdf"

            if generated_pdf.exists():
                generated_pdf.rename(pdf_path)
                return True

            print(f"LibreOffice output: {result.stdout.decode()}")
            print(f"LibreOffice error: {result.stderr.decode()}")
            return False

        except subprocess.TimeoutExpired:
            print("LibreOffice conversion timeout")
            return False
        except FileNotFoundError:
            print("LibreOffice no encontrado. Instalar con: sudo apt-get install libreoffice")
            return False
        except Exception as e:
            print(f"Error convirtiendo PPTX a PDF: {e}")
            return False

    def _convert_pdf_to_images(self, pdf_path: Path, output_dir: Path, class_id: int) -> list:
        """Convierte PDF a imágenes PNG"""
        try:
            # Convertir PDF a imágenes (una por página)
            images = convert_from_path(
                pdf_path,
                dpi=150,  # Calidad de imagen
                fmt='png'
            )

            slide_urls = []

            for i, image in enumerate(images):
                # Guardar imagen
                image_filename = f'slide_{i+1}.png'
                image_path = output_dir / image_filename

                # Optimizar imagen
                image = self._optimize_image(image)
                image.save(image_path, 'PNG', optimize=True)

                # Cerrar imagen para liberar memoria
                image.close()

                # Generar URL relativa (accesible desde el frontend)
                relative_url = f'/static/presentations/{class_id}/{image_filename}'
                slide_urls.append(relative_url)

            # Forzar garbage collection después de procesar todas las imágenes
            gc.collect()

            return slide_urls

        except Exception as e:
            print(f"Error convirtiendo PDF a imágenes: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _optimize_image(self, image, max_width=1920, max_height=1080):
        """Optimiza el tamaño de la imagen manteniendo aspect ratio"""
        width, height = image.size

        # Calcular nuevo tamaño si excede el máximo
        if width > max_width or height > max_height:
            ratio = min(max_width / width, max_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return image

    def delete_presentation_images(self, class_id: int) -> bool:
        """Elimina todas las imágenes de una presentación"""
        try:
            presentation_dir = self.presentations_folder / str(class_id)
            if presentation_dir.exists():
                import shutil
                shutil.rmtree(presentation_dir)
                return True
            return False
        except Exception as e:
            print(f"Error eliminando imágenes de presentación: {e}")
            return False


# Instancia global del convertidor
converter = PresentationConverter()


def convert_presentation_async(class_id: int, pptx_path: str):
    """
    Función auxiliar para convertir presentación de forma asíncrona
    Puede ser llamada desde una tarea en background (ej: Celery)
    """
    return converter.convert_presentation(class_id, pptx_path)
