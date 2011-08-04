DROP TABLE IF EXISTS `reptest`;

CREATE TABLE `reptest` (

                     `ID` int             NOT NULL AUTO_INCREMENT,
                `v_float` float           ,
                 `v_blob` blob            ,
                 `v_text` text(8000)      ,
                 
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `unsignedtest` (

                     `ID` int             NOT NULL AUTO_INCREMENT,
                  `v_int` int             ,
                 `v_uint` int unsigned    ,
                 
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `testA` (

                     `ID` int             NOT NULL AUTO_INCREMENT,
                 
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `testB` (

                     `ID` int unsigned    NOT NULL AUTO_INCREMENT,
                 
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `vchartest` (
                     `ID` int unsigned    NOT NULL AUTO_INCREMENT,
                     
                     `v1` varchar(20)     NOT NULL ,
                     `v2` varchar(1024)   NOT NULL ,
                     
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `vchartest`;

CREATE TABLE `vchartest` (
                     `ID` int unsigned    NOT NULL AUTO_INCREMENT,
                     
                     `v1` char(100)  NOT NULL ,
                     `v2` char(255)  NOT NULL ,
                     
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

show master status;

insert into `vchartest` (`v1`,`v2`) value ('a','b');

