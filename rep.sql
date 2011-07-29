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
