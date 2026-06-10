-- -----------------------------------------------------
-- Table `mydb`.`Пациенты`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Пациенты` (
  `id_пациента` INT NOT NULL AUTO_INCREMENT,  -- убрал NULL
  `фамилия` VARCHAR(50) NOT NULL,
  `имя` VARCHAR(50) NOT NULL,
  `отчество` VARCHAR(50) NULL,
  `пол` ENUM('М', 'Ж') NULL,
  `дата_рождения` DATE NULL,
  `полис` VARCHAR(20) NULL,
  `телефон` VARCHAR(20) NULL,
  PRIMARY KEY (`id_пациента`),
  UNIQUE INDEX `полис_UNIQUE` (`полис` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Врачи`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Врачи` (
  `id_врача` INT NOT NULL AUTO_INCREMENT,  -- убрал NULL
  `фамилия` VARCHAR(50) NOT NULL,
  `имя` VARCHAR(50) NOT NULL,
  `отчество` VARCHAR(50) NULL,
  `специализация` VARCHAR(100) NULL,
  `кабинет` VARCHAR(10) NULL,
  PRIMARY KEY (`id_врача`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Расписание`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Расписание` (
  `id_расписания` INT NOT NULL AUTO_INCREMENT,  -- убрал NULL
  `день_недели` TINYINT NULL,  -- убрал (7) - лишнее
  `время` TIME NOT NULL,
  `кабинет` VARCHAR(10) NULL,
  `id_врача` INT NULL,
  PRIMARY KEY (`id_расписания`),
  CONSTRAINT `fk_расписание_врачи`
    FOREIGN KEY (`id_врача`)
    REFERENCES `mydb`.`Врачи` (`id_врача`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Записи_на_приём`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Записи_на_приём` (
  `id_записи` INT NOT NULL AUTO_INCREMENT,  -- убрал NULL
  `дата` DATE NOT NULL,
  `время` TIME NOT NULL,
  `статус` VARCHAR(20) NULL,
  `id_пациента` INT NULL,
  `id_расписания` INT NULL,  -- добавил недостающий внешний ключ
  PRIMARY KEY (`id_записи`),
  CONSTRAINT `fk_записи_пациенты`
    FOREIGN KEY (`id_пациента`)
    REFERENCES `mydb`.`Пациенты` (`id_пациента`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_записи_расписание`
    FOREIGN KEY (`id_расписания`)
    REFERENCES `mydb`.`Расписание` (`id_расписания`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Диагнозы`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Диагнозы` (
  `id_диагноза` INT NOT NULL AUTO_INCREMENT,  -- убрал NULL
  `код_мкб` VARCHAR(10) NOT NULL,
  `название` VARCHAR(200) NOT NULL,
  PRIMARY KEY (`id_диагноза`),
  UNIQUE INDEX `код_мкб_UNIQUE` (`код_мкб` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Приёмы`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Приёмы` (
  `id_приёма` INT NOT NULL AUTO_INCREMENT,  -- убрал NULL
  `жалобы` TEXT NULL,
  `лечение` TEXT NULL,
  `id_записи` INT NULL,
  `id_диагноза` INT NULL,
  PRIMARY KEY (`id_приёма`),
  CONSTRAINT `fk_приёмы_записи`
    FOREIGN KEY (`id_записи`)
    REFERENCES `mydb`.`Записи_на_приём` (`id_записи`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_приёмы_диагнозы`
    FOREIGN KEY (`id_диагноза`)
    REFERENCES `mydb`.`Диагнозы` (`id_диагноза`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;