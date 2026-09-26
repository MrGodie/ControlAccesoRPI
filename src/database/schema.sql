-- =====================================================
-- Sistema de control de acceso
-- Esquema MySQL conforme a docs/data.md
-- =====================================================

CREATE DATABASE IF NOT EXISTS control_acceso
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE control_acceso;

-- -----------------------------------------------------
-- Tabla: roles
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
  id           INT          NOT NULL AUTO_INCREMENT,
  nombre       VARCHAR(50)  NOT NULL,
  descripcion  VARCHAR(255),
  PRIMARY KEY (id)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Tabla: usuarios
-- Relación: ROLES ||--o{ USUARIOS : "tiene"
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
  id               INT          NOT NULL AUTO_INCREMENT,
  nombre           VARCHAR(100) NOT NULL,
  credencial_hash  VARCHAR(255) NOT NULL,
  rol_id           INT          NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_usuarios_roles
    FOREIGN KEY (rol_id) REFERENCES roles (id)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Tabla: intentos_acceso
-- Relación: USUARIOS ||--o{ INTENTOS_ACCESO : "genera"
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS intentos_acceso (
  id          INT          NOT NULL AUTO_INCREMENT,
  usuario_id  INT          NOT NULL,
  metodo      VARCHAR(20)  NOT NULL,
  resultado   VARCHAR(30)  NOT NULL,
  fecha_hora  DATETIME     NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_intentos_usuarios
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE = InnoDB;