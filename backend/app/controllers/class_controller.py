"""
Class Controller - Controlador para gestión de clases
"""
from flask import request, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from app.models.class_model import Class
from app.models.user import User
from app.database import get_db
import os
from datetime import datetime


ALLOWED_EXTENSIONS = {'pptx', 'ppt'}
UPLOAD_FOLDER = 'static/uploads'
PRESENTATIONS_FOLDER = 'static/presentations'


def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_class(user_id: int):
    """
    POST /api/classes
    Crea una nueva clase con presentación
    """
    db: Session = next(get_db())

    try:
        # Validar archivo
        if 'file' not in request.files:
            return jsonify({'error': 'No se proporcionó archivo'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Archivo vacío'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Formato de archivo no permitido'}), 400

        # Obtener datos del formulario
        title = request.form.get('title')
        subject = request.form.get('subject')
        level = request.form.get('level')
        description = request.form.get('description', '')

        # Validar campos requeridos
        if not all([title, subject, level]):
            return jsonify({'error': 'Campos requeridos faltantes'}), 400

        # Guardar archivo
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{user_id}_{timestamp}_{filename}"

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)

        # Obtener tamaño del archivo
        file_size = os.path.getsize(file_path)

        # Crear clase en BD
        new_class = Class(
            user_id=user_id,
            title=title,
            subject=subject,
            level=level,
            description=description,
            file_name=filename,
            file_path=file_path,
            file_size=file_size,
            slides_count=0  # Se actualizará después de convertir
        )

        db.add(new_class)
        db.commit()
        db.refresh(new_class)

        # Convertir PPTX a imágenes
        from app.services.presentation_service import converter
        conversion_result = converter.convert_presentation(new_class.id, file_path)

        if not conversion_result['success']:
            # Si falla la conversión, eliminar la clase
            db.delete(new_class)
            db.commit()
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({
                'error': 'Error al procesar la presentación',
                'details': conversion_result.get('error')
            }), 500

        return jsonify({
            'message': 'Clase creada exitosamente',
            'class': new_class.to_dict(),
            'slides_count': conversion_result['total_slides']
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def get_classes(user_id: int):
    """
    GET /api/classes
    Obtiene todas las clases del usuario
    """
    db: Session = next(get_db())

    try:
        classes = db.query(Class).filter(Class.user_id == user_id).all()

        return jsonify({
            'classes': [cls.to_dict() for cls in classes],
            'total': len(classes)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def get_class_by_id(user_id: int, class_id: int):
    """
    GET /api/classes/<id>
    Obtiene una clase específica
    """
    db: Session = next(get_db())

    try:
        class_obj = db.query(Class).filter(
            Class.id == class_id,
            Class.user_id == user_id
        ).first()

        if not class_obj:
            return jsonify({'error': 'Clase no encontrada'}), 404

        return jsonify({
            'class': class_obj.to_dict(include_instances=True)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def update_class(user_id: int, class_id: int):
    """
    PUT /api/classes/<id>
    Actualiza una clase
    """
    db: Session = next(get_db())

    try:
        class_obj = db.query(Class).filter(
            Class.id == class_id,
            Class.user_id == user_id
        ).first()

        if not class_obj:
            return jsonify({'error': 'Clase no encontrada'}), 404

        data = request.get_json()

        # Actualizar campos permitidos
        if 'title' in data:
            class_obj.title = data['title']
        if 'subject' in data:
            class_obj.subject = data['subject']
        if 'level' in data:
            class_obj.level = data['level']
        if 'description' in data:
            class_obj.description = data['description']

        class_obj.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(class_obj)

        return jsonify({
            'message': 'Clase actualizada exitosamente',
            'class': class_obj.to_dict()
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def delete_class(user_id: int, class_id: int):
    """
    DELETE /api/classes/<id>
    Elimina una clase
    """
    db: Session = next(get_db())

    try:
        class_obj = db.query(Class).filter(
            Class.id == class_id,
            Class.user_id == user_id
        ).first()

        if not class_obj:
            return jsonify({'error': 'Clase no encontrada'}), 404

        # Eliminar archivos físicos
        try:
            # Eliminar archivo PPTX original
            if class_obj.file_path and os.path.exists(class_obj.file_path):
                os.remove(class_obj.file_path)

            # Eliminar carpeta de slides convertidas (imágenes PNG)
            slides_folder = os.path.join(PRESENTATIONS_FOLDER, str(class_id))
            if os.path.exists(slides_folder):
                import shutil
                shutil.rmtree(slides_folder)
        except Exception as e:
            print(f"Error eliminando archivos: {e}")

        db.delete(class_obj)
        db.commit()

        return jsonify({'message': 'Clase eliminada exitosamente'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
