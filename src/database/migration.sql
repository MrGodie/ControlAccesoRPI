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