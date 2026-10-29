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