# db.py (nuevo módulo)
import mysql.connector
from mysql.connector import Error

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="control_acceso_app",
        password="",  # cargar desde variable de entorno, no hardcodear
        database="control_acceso"
    )

def obtener_usuario_por_credencial(identificador, credencial_hash):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT u.id, u.nombre, r.nombre AS rol "
        "FROM usuarios u JOIN roles r ON u.rol_id = r.id "
        "WHERE u.identificador = %s AND u.credencial_hash = %s AND u.activo = TRUE",
        (identificador, credencial_hash)
    )
    usuario = cursor.fetchone()
    cursor.close()
    conexion.close()
    return usuario  # None si no existe