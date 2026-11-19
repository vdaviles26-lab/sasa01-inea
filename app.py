import io
import os
import csv
import json
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

# Estilo institucional: Azul rey (#002395) en Helvetica Bold tamaño 8
COLOR_TEXTO = colors.Color(0.0, 0.14, 0.58)
DB_JSON_PATH = "data/registros_sasa01.json"

def cargar_registros():
    if not os.path.exists(DB_JSON_PATH):
        return []
    try:
        with open(DB_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def guardar_registro_historial(datos, pdf_url):
    registros = cargar_registros()
    registro_limpio = {k: v for k, v in datos.items() if k != "firma_educanda"}
    registro_limpio["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
    registro_limpio["fecha_captura"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    registro_limpio["pdf_url"] = pdf_url
    registros.insert(0, registro_limpio)
    os.makedirs("data", exist_ok=True)
    with open(DB_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)

def generar_capa_sasa01(datos):
    """
    Genera el PDF tamaño Carta (2 páginas) con los datos capturados en las
    coordenadas exactas del formato SASA-01 para imprimir sobre el original.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter  # 215.9 mm x 279.4 mm

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(COLOR_TEXTO)

    def escribir(x_mm, y_sup_mm, texto):
        if texto is not None and str(texto).strip() != "":
            x_pt = x_mm * mm
            y_pt = height - (y_sup_mm * mm)
            c.drawString(x_pt, y_pt, str(texto).upper())

    # =========================================================================
    # PÁGINA 1: ENCABEZADO, DATOS GENERALES, DOMICILIO, DISCAPACIDAD, OCUPACIÓN
    # =========================================================================
    escribir(48, 25, datos.get("coordinacion_zona", ""))
    escribir(152, 25, datos.get("fecha_dia", ""))
    escribir(167, 25, datos.get("fecha_mes", ""))
    escribir(182, 25, datos.get("fecha_anio", ""))

    # Datos Generales
    escribir(22, 43, datos.get("primer_apellido", ""))
    escribir(82, 43, datos.get("segundo_apellido", ""))
    escribir(142, 43, datos.get("nombre", ""))

    escribir(38, 53, datos.get("nac_dia", ""))
    escribir(51, 53, datos.get("nac_mes", ""))
    escribir(64, 53, datos.get("nac_anio", ""))
    escribir(95, 53, datos.get("rfe", ""))

    # Sexo
    sexo = datos.get("sexo", "").lower()
    if "mujer" in sexo:
        escribir(24, 62, "X")
    elif "hombre" in sexo:
        escribir(48, 62, "X")
    elif "binario" in sexo:
        escribir(74, 62, "X")

    escribir(112, 62, datos.get("nacionalidad", "MEXICANA"))
    escribir(158, 62, datos.get("entidad_nacimiento", ""))

    # Estado Civil
    estado_civil = datos.get("estado_civil", "").lower()
    mapa_ec = {
        "soltero": 24, "casado": 48, "concubino": 74,
        "separado": 100, "divorciado": 126, "viudo": 152
    }
    for clave, pos_x in mapa_ec.items():
        if clave in estado_civil:
            escribir(pos_x, 71, "X")
            break
    escribir(185, 71, datos.get("num_hijos", ""))

    # Lengua y cultura
    escribir(112, 80, datos.get("pais_nacimiento", "MÉXICO"))
    if datos.get("habla_espanol") == "Si":
        escribir(24, 88, "X")
    if datos.get("habla_lengua_indigena") == "Si":
        escribir(65, 88, "X")
        escribir(95, 88, datos.get("cual_lengua", ""))
    if datos.get("considera_indigena") == "Si":
        escribir(24, 96, "X")
    if datos.get("afrodescendiente") == "Si":
        escribir(65, 96, "X")
    if datos.get("otro_idioma") == "Si":
        escribir(112, 96, "X")
        escribir(145, 96, datos.get("cual_otro_idioma", ""))

    # Domicilio
    escribir(25, 118, datos.get("vialidad_tipo", ""))
    escribir(75, 118, datos.get("vialidad_nombre", ""))
    escribir(155, 118, datos.get("num_ext", ""))
    escribir(182, 118, datos.get("num_int", ""))

    escribir(25, 130, datos.get("asentamiento_tipo", ""))
    escribir(75, 130, datos.get("asentamiento_nombre", ""))

    escribir(25, 142, datos.get("entre_vialidad_1", ""))
    escribir(115, 142, datos.get("entre_vialidad_2", ""))

    escribir(25, 152, datos.get("cp", ""))
    escribir(65, 152, datos.get("localidad", ""))
    escribir(125, 152, datos.get("municipio", ""))
    escribir(172, 152, datos.get("entidad_federativa", "MÉXICO"))

    # Contacto y acceso digital
    escribir(45, 162, datos.get("telefono", ""))
    if datos.get("acceso_computo") == "Si":
        escribir(145, 162, "X")
    escribir(45, 170, datos.get("correo_personal", ""))
    if datos.get("acceso_internet") == "Si":
        escribir(145, 170, "X")
    escribir(45, 178, datos.get("correo_inea", ""))

    # Discapacidad
    discapacidad = datos.get("discapacidad", "No").lower()
    if "no" in discapacidad:
        escribir(24, 188, "X")
    else:
        escribir(45, 188, "X")
        if "motriz" in discapacidad:
            escribir(24, 198, "X")
        if "visual" in discapacidad:
            escribir(74, 198, "X")
        if "auditiva" in discapacidad:
            escribir(135, 198, "X")
        if "intelectual" in discapacidad:
            escribir(24, 208, "X")
        if "psicosocial" in discapacidad:
            escribir(74, 208, "X")

    # Trabajo y ocupación
    ocupacion = datos.get("ocupacion", "").lower()
    if any(k in ocupacion for k in ["jubilado", "desempleado", "estudiante", "no"]):
        escribir(24, 222, "X")
        escribir(65, 222, datos.get("ocupacion", ""))
    elif ocupacion:
        escribir(24, 232, "X")
        escribir(65, 232, datos.get("ocupacion", ""))

    c.showPage()
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(COLOR_TEXTO)

    # =========================================================================
    # PÁGINA 2: ANTECEDENTES, NIVEL, SERVICIO, FIRMAS Y TALÓN
    # =========================================================================
    antecedentes = datos.get("antecedentes_escolares", "").lower()
    if "sin estudios" in antecedentes:
        escribir(24, 22, "X")
    elif "primaria" in antecedentes:
        escribir(68, 22, "X")
        escribir(95, 22, datos.get("grado_antecedente", ""))
    elif "secundaria" in antecedentes:
        escribir(125, 22, "X")
        escribir(155, 22, datos.get("grado_antecedente", ""))

    # Nivel al que ingresa
    nivel = datos.get("nivel_ingreso", "").lower()
    if "alfabetizacion" in nivel or "alfabetización" in nivel:
        if "bilingüe" in nivel or "bilingue" in nivel:
            escribir(145, 34, "X")
            escribir(175, 40, datos.get("etnia_lengua", ""))
        else:
            escribir(24, 34, "X")
    elif "primaria" in nivel:
        escribir(68, 34, "X")
    elif "secundaria" in nivel:
        escribir(105, 34, "X")

    # Servicio educativo
    servicio = datos.get("servicio_educativo", "").lower()
    if "diagnóstico" in servicio or "diagnostico" in servicio:
        escribir(24, 48, "X")
    elif "saberes" in servicio:
        escribir(78, 48, "X")
    elif "atención" in servicio or "atencion" in servicio:
        escribir(135, 48, "X")

    escribir(45, 56, datos.get("subproyecto", ""))
    escribir(125, 56, datos.get("dependencia", ""))

    # Motivo y difusión
    escribir(45, 88, datos.get("motivo_estudio", ""))
    escribir(45, 100, datos.get("como_se_entero", ""))

    # Unidad Operativa y Círculo de Estudio
    escribir(45, 112, datos.get("unidad_operativa", ""))
    escribir(135, 112, datos.get("circulo_estudio", ""))

    # Firmas
    nombre_completo = f"{datos.get('nombre', '')} {datos.get('primer_apellido', '')} {datos.get('segundo_apellido', '')}".strip()
    escribir(35, 185, nombre_completo)
    escribir(35, 205, datos.get("nombre_tutor", ""))
    escribir(125, 205, datos.get("nombre_incorpora", ""))
    escribir(35, 225, datos.get("nombre_coordinador", ""))
    escribir(125, 225, datos.get("nombre_acreditacion", ""))
    escribir(80, 238, datos.get("nombre_capturo", ""))

    # Estampado de Firma Digital
    firma_b64 = datos.get("firma_educanda", "")
    if firma_b64 and "," in firma_b64:
        try:
            firma_b64 = firma_b64.split(",")[1]
            imagen_bytes = base64.b64decode(firma_b64)
            imagen_firma = ImageReader(io.BytesIO(imagen_bytes))
            x_firma = 120 * mm
            y_firma = height - (188 * mm)
            c.drawImage(imagen_firma, x_firma, y_firma, width=55*mm, height=18*mm, mask='auto')
        except Exception as e:
            print(f"Error firma: {e}")

    # Talón de correo institucional
    escribir(75, 253, nombre_completo)
    escribir(55, 259, datos.get("correo_inea", ""))
    escribir(145, 259, datos.get("password_inea", ""))

    escribir(75, 268, nombre_completo)
    escribir(55, 273, datos.get("correo_inea", ""))
    escribir(145, 273, datos.get("fecha_entrega_correo", ""))

    c.save()
    buffer.seek(0)
    return buffer

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/generar_sasa01', methods=['POST'])
def endpoint_generar_sasa01():
    try:
        datos = request.get_json(force=True)
        pdf_buffer = generar_capa_sasa01(datos)
        
        os.makedirs("static/pdfs", exist_ok=True)
        identificador = datos.get("rfe") or f"{datos.get('primer_apellido', 'educando')}_{datos.get('nombre', '')}"
        identificador = "".join(c for c in identificador if c.isalnum() or c in ('_', '-'))
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"SASA01_{identificador}_{timestamp}.pdf"
        filepath = os.path.join("static/pdfs", filename)
        
        with open(filepath, "wb") as f:
            f.write(pdf_buffer.getbuffer())

        pdf_url = f"/static/pdfs/{filename}"
        guardar_registro_historial(datos, pdf_url)

        return jsonify({"status": "ok", "pdf_url": pdf_url}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/historial', methods=['GET'])
def api_historial():
    return jsonify(cargar_registros())

@app.route('/exportar_csv', methods=['GET'])
def exportar_csv():
    registros = cargar_registros()
    output = io.StringIO()
    output.write('﻿')
    
    campos = [
        "fecha_captura", "coordinacion_zona", "primer_apellido", "segundo_apellido", "nombre",
        "nac_dia", "nac_mes", "nac_anio", "rfe", "sexo", "estado_civil", "num_hijos",
        "entidad_nacimiento", "habla_espanol", "habla_lengua_indigena", "cual_lengua",
        "considera_indigena", "afrodescendiente", "vialidad_tipo", "vialidad_nombre",
        "num_ext", "num_int", "asentamiento_tipo", "asentamiento_nombre", "cp",
        "localidad", "municipio", "telefono", "correo_personal", "discapacidad",
        "ocupacion", "antecedentes_escolares", "grado_antecedente", "nivel_ingreso",
        "servicio_educativo", "unidad_operativa", "circulo_estudio", "nombre_incorpora",
        "correo_inea", "pdf_url"
    ]
    
    writer = csv.DictWriter(output, fieldnames=campos, extrasaction='ignore')
    writer.writeheader()
    for reg in registros:
        writer.writerow(reg)
        
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    fecha_hoy = datetime.now().strftime("%Y%m%d")
    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"Base_Registros_SASA01_{fecha_hoy}.csv"
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
