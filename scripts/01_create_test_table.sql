DROP TABLE IF EXISTS `tests`;

CREATE TABLE IF NOT EXISTS `tests`
(
  `id`               INT(20) AUTO_INCREMENT,
  `name`             VARCHAR(20) NOT NULL,
  `date`             DATE NOT NULL,
  PRIMARY KEY (`id`, `date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin
PARTITION BY RANGE COLUMNS(date) (
    PARTITION p202001 VALUES LESS THAN ('2020-02-01') ENGINE = InnoDB,
    PARTITION p202002 VALUES LESS THAN ('2020-03-01') ENGINE = InnoDB,
    PARTITION p202003 VALUES LESS THAN ('2020-04-01') ENGINE = InnoDB,
    PARTITION p202004 VALUES LESS THAN ('2020-05-01') ENGINE = InnoDB,
    PARTITION p202005 VALUES LESS THAN ('2020-06-01') ENGINE = InnoDB,
    PARTITION p202006 VALUES LESS THAN ('2020-07-01') ENGINE = InnoDB
);