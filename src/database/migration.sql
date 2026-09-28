USE control_acceso;
 
-- -----------------------------------------------------
-- 1. Intentos sin usuario asociado
--    Una clave no reconocida o un error de sistema no tienen
--    usuario: usuario_id debe aceptar NULL, o esos intentos
--    no se podrían registrar.
-- -----------------------------------------------------
ALTER TABLE intentos_acceso
  MODIFY usuario_id INT NULL;
 
-- -----------------------------------------------------
-- 2. Fecha por defecto
--    Permite insertar intentos a mano (pruebas) y evita
--    depender de que el código siempre envíe la fecha.
-- -----------------------------------------------------
ALTER TABLE intentos_acceso
  MODIFY fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
 
-- -----------------------------------------------------
-- 3. Una clave identifica a un único usuario
--    Sin esto, dos usuarios con la misma clave harían
--    ambigua la consulta de validación.
-- -----------------------------------------------------
ALTER TABLE usuarios
  ADD UNIQUE INDEX IF NOT EXISTS uq_usuarios_credencial (credencial_hash);
 
-- -----------------------------------------------------
-- 4. Roles base (solo se insertan si no existen)
--    roles.nombre no es UNIQUE en el schema, por eso se usa
--    NOT EXISTS en lugar de INSERT IGNORE.
-- -----------------------------------------------------
INSERT INTO roles (nombre, descripcion, acceso_permitido)
SELECT 'administrador', 'Acceso completo al sistema', TRUE FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'administrador');
 
INSERT INTO roles (nombre, descripcion, acceso_permitido)
SELECT 'usuario_estandar', 'Acceso a operaciones básicas', TRUE FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'usuario_estandar');
 
INSERT INTO roles (nombre, descripcion, acceso_permitido)
SELECT 'visitante', 'Registrado en el sistema pero sin acceso al punto', FALSE FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'visitante');