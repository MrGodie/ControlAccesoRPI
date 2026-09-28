CREATE DATABASE IF NOT EXISTS control_acceso
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE control_acceso;

-- -----------------------------------------------------
-- Tabla: roles
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
-- Roles base
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