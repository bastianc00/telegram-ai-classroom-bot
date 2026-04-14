"""
Gemini AI Service - Servicio para generar ejemplos con IA
"""
import os
import gc  # Garbage collector para liberar memoria
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configuración
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)


def generate_example_options(topic: str, slide_content: str = "", context: str = "", num_options: int = 3) -> list[str]:
    """
    Genera opciones de ejemplos sobre un tema usando Gemini AI

    Args:
        topic: Tema principal del ejemplo solicitado
        slide_content: Contenido extraído de las diapositivas hasta la actual
        context: Contexto adicional (materia, nivel)
        num_options: Número de opciones a generar (default: 3)

    Returns:
        Lista de ejemplos generados
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # Construir prompt
        prompt = f"""Eres un asistente educacional que ayuda a profesores a generar ejemplos claros y didácticos.

Tema solicitado: {topic}
{f'Contexto: {context}' if context else ''}

Contenido de las diapositivas presentadas hasta ahora:
{slide_content[:2000] if slide_content else 'No disponible'}

Genera {num_options} ejemplos diferentes que sean:
- Claros y fáciles de entender
- Relevantes al tema solicitado
- Basados en el contenido de las diapositivas presentadas
- Apropiados para uso educativo
- Concisos (máximo 2-3 párrafos cada uno)

Formato de respuesta: Devuelve SOLO los {num_options} ejemplos, separados por "---" (tres guiones).
No incluyas numeración, títulos ni texto adicional.
"""

        response = model.generate_content(prompt)

        # Procesar respuesta
        examples_text = response.text.strip()
        examples = [ex.strip() for ex in examples_text.split('---') if ex.strip()]

        # Asegurar que tengamos exactamente num_options ejemplos
        if len(examples) < num_options:
            # Si no generó suficientes, completar con placeholder
            while len(examples) < num_options:
                examples.append(f"Ejemplo sobre {topic}")

        return examples[:num_options]

    except Exception as e:
        import traceback; traceback.print_exc(); print(f"Error generando ejemplos con Gemini: {e}")
        # Retornar ejemplos por defecto en caso de error
        return [
            f"Ejemplo 1 sobre {topic}",
            f"Ejemplo 2 sobre {topic}",
            f"Ejemplo 3 sobre {topic}"
        ]
    finally:
        # Forzar garbage collection para liberar memoria de la respuesta AI
        gc.collect()


def enhance_example(example: str, topic: str) -> dict:
    """
    Mejora un ejemplo seleccionado y genera contenido estructurado para la diapositiva

    Args:
        example: Texto del ejemplo seleccionado
        topic: Tema del ejemplo

    Returns:
        Dict con título, contenido y puntos clave
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        prompt = f"""Eres un asistente educacional. Te han dado este ejemplo sobre "{topic}":

{example}

Estructura este ejemplo para una diapositiva educativa con:
1. Un título corto y descriptivo (máximo 8 palabras)
2. El contenido principal del ejemplo (2-3 párrafos máximo)
3. 3-4 puntos clave o conclusiones

Formato de respuesta (usa exactamente este formato):
TITULO: [título aquí]
CONTENIDO: [contenido aquí]
PUNTOS:
- [punto 1]
- [punto 2]
- [punto 3]
- [punto 4]
"""

        response = model.generate_content(prompt)

        # Parsear respuesta
        text = response.text.strip()

        title = ""
        content = ""
        key_points = []

        lines = text.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith('TITULO:'):
                title = line.replace('TITULO:', '').strip()
                current_section = 'title'
            elif line.startswith('CONTENIDO:'):
                content = line.replace('CONTENIDO:', '').strip()
                current_section = 'content'
            elif line.startswith('PUNTOS:'):
                current_section = 'points'
            elif line.startswith('-') and current_section == 'points':
                key_points.append(line[1:].strip())
            elif current_section == 'content' and line:
                content += '\n' + line

        return {
            'title': title or f"Ejemplo: {topic}",
            'content': content or example,
            'key_points': key_points or []
        }

    except Exception as e:
        print(f"Error mejorando ejemplo: {e}")
        return {
            'title': f"Ejemplo: {topic}",
            'content': example,
            'key_points': []
        }
    finally:
        gc.collect()


def generate_question_options(slide_content: str, question_type: str = "multiple-choice", custom_prompt: str = "", num_options: int = 3) -> list[str]:
    """
    Genera opciones de preguntas basadas en el contenido de las diapositivas

    Args:
        slide_content: Texto extraído de las diapositivas hasta la actual
        question_type: "multiple-choice" o "open"
        custom_prompt: Prompt o instrucciones personalizadas del profesor (opcional)
        num_options: Número de opciones a generar (default: 3)

    Returns:
        Lista de preguntas generadas
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # Construir prompt según el tipo de pregunta
        if question_type == "multiple-choice":
            prompt = f"""Eres un asistente educacional que ayuda a profesores a crear preguntas de evaluación.

Contenido de las diapositivas:
{slide_content[:2000]}  # Limitar a 2000 caracteres

{f'Instrucciones adicionales del profesor: {custom_prompt}' if custom_prompt else ''}

Genera {num_options} preguntas diferentes de opción múltiple (4 alternativas) basadas en el contenido presentado.

Cada pregunta debe:
- Ser clara y específica
- Tener 4 alternativas (A, B, C, D)
- Tener una sola respuesta correcta
- Ser apropiada para evaluar comprensión del contenido

Formato de respuesta: Devuelve SOLO las {num_options} preguntas, separadas por "---" (tres guiones).
Cada pregunta debe incluir:
- La pregunta
- Las 4 alternativas
- Indicar cuál es la correcta

Ejemplo:
¿Cuál es la definición correcta de X?
A) Opción incorrecta
B) Opción correcta
C) Opción incorrecta
D) Opción incorrecta
Respuesta correcta: B

No incluyas numeración de preguntas ni texto adicional."""

        else:  # open
            prompt = f"""Eres un asistente educacional que ayuda a profesores a crear preguntas de evaluación.

Contenido de las diapositivas:
{slide_content[:2000]}  # Limitar a 2000 caracteres

{f'Instrucciones adicionales del profesor: {custom_prompt}' if custom_prompt else ''}

Genera {num_options} preguntas abiertas diferentes basadas en el contenido presentado.

Cada pregunta debe:
- Ser clara y específica
- Requerir reflexión y desarrollo
- Evaluar comprensión profunda del contenido
- Ser apropiada para respuesta escrita

Formato de respuesta: Devuelve SOLO las {num_options} preguntas, separadas por "---" (tres guiones).
No incluyas numeración ni texto adicional.

Ejemplo:
Explique el concepto de X y su relación con Y, proporcionando ejemplos concretos."""

        response = model.generate_content(prompt)

        # Procesar respuesta
        questions_text = response.text.strip()
        questions = [q.strip() for q in questions_text.split('---') if q.strip()]

        # Asegurar que tengamos exactamente num_options preguntas
        if len(questions) < num_options:
            while len(questions) < num_options:
                questions.append(f"Pregunta sobre el contenido presentado")

        return questions[:num_options]

    except Exception as e:
        print(f"Error generando preguntas con Gemini: {e}")
        # Retornar preguntas por defecto en caso de error
        return [
            "Pregunta 1 sobre el contenido",
            "Pregunta 2 sobre el contenido",
            "Pregunta 3 sobre el contenido"
        ]
    finally:
        gc.collect()


def enhance_question(question: str, question_type: str) -> dict:
    """
    Mejora una pregunta seleccionada y genera contenido estructurado para la diapositiva

    Args:
        question: Texto de la pregunta seleccionada
        question_type: "multiple-choice" o "open"

    Returns:
        Dict con título, pregunta, alternativas (si aplica)
    """
    try:
        # Para preguntas, no necesitamos mejorar mucho, solo estructurar
        if question_type == "multiple-choice":
            # Parsear la pregunta y extraer alternativas
            lines = question.split('\n')
            question_text = lines[0] if lines else question
            alternatives = []
            correct_answer = ""

            for line in lines[1:]:
                line = line.strip()
                if line.startswith(('A)', 'B)', 'C)', 'D)')):
                    alternatives.append(line)
                elif line.startswith('Respuesta correcta:'):
                    correct_answer = line.replace('Respuesta correcta:', '').strip()

            return {
                'title': "Pregunta de Evaluación",
                'question': question_text,
                'type': 'multiple-choice',
                'alternatives': alternatives,
                'correct_answer': correct_answer
            }
        else:  # open
            return {
                'title': "Pregunta de Desarrollo",
                'question': question,
                'type': 'open',
                'alternatives': [],
                'correct_answer': ""
            }

    except Exception as e:
        print(f"Error mejorando pregunta: {e}")
        return {
            'title': "Pregunta de Evaluación",
            'question': question,
            'type': question_type,
            'alternatives': [],
            'correct_answer': ""
        }
    finally:
        gc.collect()


def generate_analogy_options(slide_content: str, context: str = "", num_options: int = 3) -> list[str]:
    """
    Genera 2-3 analogías simples para explicar el concepto de la diapositiva actual

    Args:
        slide_content: Contenido extraído de la diapositiva actual
        context: Contexto adicional (materia, nivel)
        num_options: Número de analogías a generar (default: 3)

    Returns:
        Lista de analogías generadas
    """
    try:
        print(f"[DEBUG generate_analogy] Starting generation with content length: {len(slide_content)}")

        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # Construir prompt - similar al de ejemplo
        prompt = f"""Genera {num_options} analogías simples y cortas para explicar el concepto principal de este contenido:

{slide_content[:1500]}

{f'Materia: {context}' if context else ''}

Cada analogía debe:
- Ser muy concisa (máximo 2 oraciones)
- Usar ejemplos cotidianos y fáciles de entender
- Comenzar con "Es como..." o "Imagina que..."

Formato: Devuelve SOLO las {num_options} analogías separadas por "---".

Ejemplo:
Es como un semáforo: cuando está verde pasas, cuando está rojo te detienes.
---
Imagina ordenar tu cuarto: primero recoges, luego guardas, finalmente limpias.
"""

        print(f"[DEBUG generate_analogy] Calling Gemini API...")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=800,
            ),
            request_options={"timeout": 30}  # 30 segundos timeout
        )
        print(f"[DEBUG generate_analogy] Received response from Gemini")

        # Procesar respuesta
        analogies_text = response.text.strip()
        analogies = [a.strip() for a in analogies_text.split('---') if a.strip()]

        # Asegurar que tenemos al menos 2 analogías
        if len(analogies) < 2:
            print(f"[WARNING] Solo se generaron {len(analogies)} analogías, se esperaban {num_options}")
            return analogies if analogies else ["No se pudo generar una analogía para este contenido."]

        return analogies[:num_options]  # Limitar al número solicitado

    except Exception as e:
        print(f"Error generating analogies: {e}")
        import traceback
        traceback.print_exc()
        return ["Error al generar analogías. Por favor intenta nuevamente."]
    finally:
        gc.collect()
