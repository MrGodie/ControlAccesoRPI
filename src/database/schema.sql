-- =====================================================
-- Sistema de control de acceso
-- Esquema MySQL/MariaDB conforme a docs/data.md
--
-- Crea la base desde cero:
--   sudo mariadb < database/schema.sql
-- Para bases ya creadas con una versión anterior del schema,
-- usar database/migracion_v2.sql
-- =====================================================

CREATE DATABASE IF NOT EXISTS control_acceso
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE control_acceso;

-- -----------------------------------------------------
-- Tabla: roles
-- acceso_permitido define si el rol puede abrir el acceso;
-- permite distinguir "identificado pero sin permiso".
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
  id               INT          NOT NULL AUTO_INCREMENT,
  nombre           VARCHAR(50)  NOT NULL,
  descripcion      VARCHAR(255),
  acceso_permitido BOOLEAN      NOT NULL DEFAULT TRUE,
  PRIMARY KEY (id)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Tabla: usuarios
-- Relación: ROLES ||--o{ USUARIOS : "tiene"
-- credencial_hash guarda SHA2-256 de la clave, nunca la clave.
-- Es UNIQUE porque la clave identifica al usuario.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
  id               INT          NOT NULL AUTO_INCREMENT,
  nombre           VARCHAR(100) NOT NULL,
  credencial_hash  VARCHAR(255) NOT NULL,
  rol_id           INT          NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_usuarios_credencial (credencial_hash),
  CONSTRAINT fk_usuarios_roles
    FOREIGN KEY (rol_id) REFERENCES roles (id)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Tabla: intentos_acceso
-- Relación: USUARIOS ||--o{ INTENTOS_ACCESO : "genera"
-- usuario_id es NULL cuando la clave no se reconoce o
-- cuando ocurre un error de sistema (no hay usuario al
-- cual asociar el intento).
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS intentos_acceso (
  id          INT          NOT NULL AUTO_INCREMENT,
  usuario_id  INT          NULL,
  metodo      VARCHAR(20)  NOT NULL,
  resultado   VARCHAR(30)  NOT NULL,
  fecha_hora  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_intentos_usuarios
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Roles base (solo se insertan si no existen)
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