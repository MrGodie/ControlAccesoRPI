CREATE DATABASE IF NOT EXISTS control_acceso
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE control_acceso;

-- -----------------------------------------------------
-- Tabla: roles
--
-- Un rol declara QUÉ PUEDE HACER quien lo tiene, en tres
-- capacidades independientes. El código pregunta por la capacidad,
-- nunca por el nombre del rol: renombrar un rol no debe cambiar los
-- permisos de nadie.
--
--   acceso_permitido  abre el punto de acceso
--   puede_gestionar   da de alta y modifica usuarios
--   puede_consultar   ve la información de otros usuarios
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
  id               INT          NOT NULL AUTO_INCREMENT,
  nombre           VARCHAR(50)  NOT NULL,
  descripcion      VARCHAR(255),
  acceso_permitido BOOLEAN      NOT NULL DEFAULT TRUE,
  puede_gestionar  BOOLEAN      NOT NULL DEFAULT FALSE,
  puede_consultar  BOOLEAN      NOT NULL DEFAULT FALSE,
  PRIMARY KEY (id),
  UNIQUE KEY uq_roles_nombre (nombre)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Tabla: usuarios
--
-- `activo` separa "qué puede hacer" (el rol) de "está habilitado"
-- (la persona). Dar de baja a alguien se hace apagando esta columna,
-- no borrando el registro: intentos_acceso apunta aquí y la bitácora
-- no debe perder a quién correspondió cada intento.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
  id               INT          NOT NULL AUTO_INCREMENT,
  nombre           VARCHAR(100) NOT NULL,
  credencial_hash  VARCHAR(255) NOT NULL,
  rol_id           INT          NOT NULL,
  activo           BOOLEAN      NOT NULL DEFAULT TRUE,
  PRIMARY KEY (id),
  UNIQUE KEY uq_usuarios_credencial (credencial_hash),
  CONSTRAINT fk_usuarios_roles
    FOREIGN KEY (rol_id) REFERENCES roles (id)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Tabla: datos_biometricos
-- Facial templates linked to a user. A user can have several
-- samples; deleting the user deletes their biometric data.
-- Only the template is stored, never the face images.
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
-- Tabla: intentos_acceso
-- metodo: 'gui' | 'botones' | 'facial'
-- usuario_id es NULL cuando no se identifica a nadie
-- (rostro o credencial no reconocidos, fallo del sistema).
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
--
--   usuario   entra al punto de acceso y nada más
--   admin     entra, y ve, registra y modifica usuarios
--   soporte   entra, y ve la información de otros, sin modificar
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
