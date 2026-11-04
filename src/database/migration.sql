USE control_acceso;

-- -----------------------------------------------------
-- Migracion: control_acceso
-- Compatible con tablas existentes.
-- -----------------------------------------------------

DROP PROCEDURE IF EXISTS migrar_control_acceso;

DELIMITER //

CREATE PROCEDURE migrar_control_acceso()
BEGIN
  -- 1. Agregar acceso_permitido si no existe.
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'roles'
      AND COLUMN_NAME = 'acceso_permitido'
  ) THEN
    ALTER TABLE roles
      ADD COLUMN acceso_permitido BOOLEAN NOT NULL DEFAULT TRUE;
  END IF;

  -- 2. Permitir intentos sin usuario asociado.
  ALTER TABLE intentos_acceso
    MODIFY COLUMN usuario_id INT NULL;

  -- 3. Fecha por defecto para los intentos.
  ALTER TABLE intentos_acceso
    MODIFY COLUMN fecha_hora DATETIME NOT NULL
    DEFAULT CURRENT_TIMESTAMP;

  -- 4. Crear índice único si no existe por nombre.
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'usuarios'
      AND INDEX_NAME = 'uq_usuarios_credencial'
  ) THEN
    ALTER TABLE usuarios
      ADD UNIQUE INDEX uq_usuarios_credencial (credencial_hash);
  END IF;
END //

DELIMITER ;

CALL migrar_control_acceso();

DROP PROCEDURE IF EXISTS migrar_control_acceso;

-- -----------------------------------------------------
-- 5. Insertar roles que todavía no existen.
-- -----------------------------------------------------

INSERT INTO roles (nombre, descripcion, acceso_permitido)
SELECT 'administrador', 'Acceso completo al sistema', TRUE
WHERE NOT EXISTS (
  SELECT 1 FROM roles WHERE nombre = 'administrador'
);

INSERT INTO roles (nombre, descripcion, acceso_permitido)
SELECT 'usuario_estandar', 'Acceso a operaciones básicas', TRUE
WHERE NOT EXISTS (
  SELECT 1 FROM roles WHERE nombre = 'usuario_estandar'
);

INSERT INTO roles (nombre, descripcion, acceso_permitido)
SELECT 'visitante', 'Registrado en el sistema pero sin acceso al punto', FALSE
WHERE NOT EXISTS (
  SELECT 1 FROM roles WHERE nombre = 'visitante'
);

-- -----------------------------------------------------
-- 6. Asegurar los permisos de los roles base.
-- -----------------------------------------------------

UPDATE roles
SET acceso_permitido = TRUE
WHERE nombre IN ('administrador', 'usuario_estandar');

UPDATE roles
SET acceso_permitido = FALSE
WHERE nombre = 'visitante';

-- -----------------------------------------------------
-- 7. Biometric data table (PIC-11).
-- Safe to run many times: it only creates the table if missing.
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS datos_biometricos (
  id              INT          NOT NULL AUTO_INCREMENT,
  usuario_id      INT          NOT NULL,
  tipo            VARCHAR(20)  NOT NULL DEFAULT 'facial',
  embedding       BLOB         NOT NULL,  -- serialized face template (bytes)
  modelo          VARCHAR(50)  NOT NULL,  -- library/model that produced it
  fecha_registro  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_biometricos_usuario (usuario_id),
  CONSTRAINT fk_biometricos_usuarios
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    ON DELETE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- 8. Permisos de la cuenta de la aplicación (PIC-74).
-- Requiere una cuenta administradora (sudo mysql), no la
-- de la aplicación. Es seguro correrla varias veces: GRANT
-- no duplica permisos que ya existen.
-- La cuenta 'control_acceso_app'@'localhost' debe existir
-- antes; esta sección no la crea. Su contraseña no va en
-- este archivo (NFR-06): vive en las variables de entorno
-- que lee db.py (DB_USER, DB_PASSWORD).
-- Permisos mínimos: sin ALL PRIVILEGES. La bitácora
-- intentos_acceso no lleva UPDATE ni DELETE a propósito:
-- los registros de acceso no se editan.
-- -----------------------------------------------------

GRANT SELECT
  ON control_acceso.roles
  TO 'control_acceso_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
  ON control_acceso.usuarios
  TO 'control_acceso_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
  ON control_acceso.datos_biometricos
  TO 'control_acceso_app'@'localhost';

GRANT SELECT, INSERT
  ON control_acceso.intentos_acceso
  TO 'control_acceso_app'@'localhost';

FLUSH PRIVILEGES;

-- =====================================================================
-- AGREGA ESTO AL FINAL DE src/database/migration.sql
-- =====================================================================

-- -----------------------------------------------------
-- 9. Tres roles con capacidades declaradas (PIC-78).
--
-- Antes había 'administrador', 'usuario_estandar' y 'visitante', y el
-- único permiso que la tabla sabía expresar era acceso_permitido: si
-- abre la puerta o no. Lo demás lo deducía el código comparando el
-- NOMBRE del rol contra un texto, así que renombrar un rol tiraba los
-- permisos en silencio y no había dónde acomodar a 'soporte'.
--
-- Ahora el rol declara tres capacidades y el código pregunta por la
-- capacidad, nunca por el nombre:
--
--   usuario   acceso                     entra y nada más
--   admin     acceso + gestionar + ver   ve, registra y modifica
--   soporte   acceso + ver               consulta sin modificar
--
-- Y usuarios.activo separa "qué puede hacer" de "está habilitado",
-- que es lo que 'visitante' fingía ser.
--
-- Orden obligatorio: usuarios.rol_id es llave foránea a roles, así que
-- primero se crean los roles nuevos, luego se reasignan los usuarios,
-- y hasta el final se borran los viejos. Al revés, MySQL rechaza el
-- DELETE y la migración se queda a medias.
--
-- Es seguro correrlo varias veces.
-- -----------------------------------------------------

-- 9.1 Columnas de capacidad en roles.
DROP PROCEDURE IF EXISTS migrar_roles_pic78;

DELIMITER //

CREATE PROCEDURE migrar_roles_pic78()
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'roles'
      AND COLUMN_NAME = 'puede_gestionar'
  ) THEN
    ALTER TABLE roles
      ADD COLUMN puede_gestionar BOOLEAN NOT NULL DEFAULT FALSE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'roles'
      AND COLUMN_NAME = 'puede_consultar'
  ) THEN
    ALTER TABLE roles
      ADD COLUMN puede_consultar BOOLEAN NOT NULL DEFAULT FALSE;
  END IF;

  -- 9.2 Bandera de alta/baja en usuarios.
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'usuarios'
      AND COLUMN_NAME = 'activo'
  ) THEN
    ALTER TABLE usuarios
      ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE;
  END IF;

  -- 9.3 El nombre del rol debe ser único: sin esto se pueden colar dos
  --     'admin' y el mapeo de abajo se vuelve ambiguo.
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'roles'
      AND INDEX_NAME = 'uq_roles_nombre'
  ) THEN
    ALTER TABLE roles
      ADD UNIQUE INDEX uq_roles_nombre (nombre);
  END IF;
END //

DELIMITER ;

CALL migrar_roles_pic78();

DROP PROCEDURE IF EXISTS migrar_roles_pic78;

-- -----------------------------------------------------
-- 9.4 Crear los tres roles definitivos.
-- -----------------------------------------------------

INSERT INTO roles (nombre, descripcion, acceso_permitido, puede_gestionar, puede_consultar)
SELECT 'usuario', 'Accede al punto con cualquiera de los métodos disponibles', TRUE, FALSE, FALSE
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'usuario');

INSERT INTO roles (nombre, descripcion, acceso_permitido, puede_gestionar, puede_consultar)
SELECT 'admin', 'Ve, registra y modifica la información de los usuarios', TRUE, TRUE, TRUE
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'admin');

INSERT INTO roles (nombre, descripcion, acceso_permitido, puede_gestionar, puede_consultar)
SELECT 'soporte', 'Consulta la información de otros usuarios sin modificarla', TRUE, FALSE, TRUE
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'soporte');

-- -----------------------------------------------------
-- 9.5 Asegurar las capacidades, por si los roles ya existían con
--     valores distintos.
-- -----------------------------------------------------

UPDATE roles SET acceso_permitido = TRUE,  puede_gestionar = FALSE, puede_consultar = FALSE
  WHERE nombre = 'usuario';
UPDATE roles SET acceso_permitido = TRUE,  puede_gestionar = TRUE,  puede_consultar = TRUE
  WHERE nombre = 'admin';
UPDATE roles SET acceso_permitido = TRUE,  puede_gestionar = FALSE, puede_consultar = TRUE
  WHERE nombre = 'soporte';

-- -----------------------------------------------------
-- 9.6 Reasignar a los usuarios que ya existen.
--
--   administrador    -> admin
--   usuario_estandar -> usuario
--   visitante        -> usuario, pero dado de baja (activo = FALSE)
--
-- 'visitante' significaba "registrado pero sin acceso al punto", algo
-- que el modelo nuevo no expresa con un rol. Esa gente pasa a usuario
-- y queda inactiva: conserva su registro y su bitácora, y sigue sin
-- poder entrar. Si alguno sí debía entrar, se reactiva a mano después:
--   UPDATE usuarios SET activo = TRUE WHERE id = <el que sea>;
-- -----------------------------------------------------

UPDATE usuarios SET activo = FALSE
 WHERE rol_id IN (SELECT id FROM (SELECT id FROM roles WHERE nombre = 'visitante') AS v);

UPDATE usuarios
   SET rol_id = (SELECT id FROM roles WHERE nombre = 'admin')
 WHERE rol_id IN (SELECT id FROM (SELECT id FROM roles WHERE nombre = 'administrador') AS a);

UPDATE usuarios
   SET rol_id = (SELECT id FROM roles WHERE nombre = 'usuario')
 WHERE rol_id IN (SELECT id FROM (SELECT id FROM roles WHERE nombre IN ('usuario_estandar', 'visitante')) AS u);

-- -----------------------------------------------------
-- 9.7 Borrar los roles viejos, ya sin usuarios colgando.
--     El NOT EXISTS evita que la llave foránea reviente si por lo que
--     sea quedó alguien sin reasignar.
-- -----------------------------------------------------

DELETE FROM roles
 WHERE nombre IN ('administrador', 'usuario_estandar', 'visitante')
   AND NOT EXISTS (SELECT 1 FROM (SELECT rol_id FROM usuarios) AS u WHERE u.rol_id = roles.id);

-- -----------------------------------------------------
-- 9.8 Verificación. Después de correr la migración:
--
--   SELECT nombre, acceso_permitido, puede_gestionar, puede_consultar
--     FROM roles ORDER BY nombre;
--   -- deben salir exactamente tres: admin, soporte, usuario
--
--   SELECT u.id, u.nombre, r.nombre AS rol, u.activo
--     FROM usuarios u JOIN roles r ON u.rol_id = r.id ORDER BY u.id;
--   -- ninguno debe quedar sin rol ni con un rol viejo
-- -----------------------------------------------------
