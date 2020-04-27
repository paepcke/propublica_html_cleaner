
DROP TABLE IF EXISTS Entities;
CREATE TABLE Entities (id varchar(100),
                       entity varchar(255),
                       entity_type varchar(255)
                       ) engine=MyISAM;

DROP TABLE IF EXISTS Metadata;
CREATE TABLE Metadata (id varchar(100),
              political tinyint,
              not_political tinyint,
              title varchar(255),
              thumbnail varchar(500),
              created_at DATETIME,
              updated_at DATETIME,
              lang varchar(20),
              images varchar(1000),
              impressions int,
              political_probability double,
              targeting varchar(1000) DEFAULT '',
              suppressed varchar(2),
              advertiser varchar(255),
              page varchar(255), 
              lower_page varchar(1000),
              targetings varchar(255),
              paid_for_by varchar(255),
              targetedness int,
              listbuilding_fundraising_proba double
              ) engine=MyISAM;

DROP TABLE IF EXISTS Messages;
CREATE TABLE Messages (id varchar(100), message text) engine=MyISAM;

DROP TABLE IF EXISTS Targets;
CREATE TABLE Targets (id varchar(100),
                      target varchar(400),
                      segment varchar(400)
                      ) engine=MyISAM;
# Load the entities

LOAD DATA LOCAL INFILE '/tmp/propub_entities.csv'
INTO TABLE Entities
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n';


# Load the message texts:

LOAD DATA LOCAL INFILE '/tmp/propub_msgs.csv'
INTO TABLE Messages
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\r\n'
IGNORE 1 LINES;

# Load the metadata

LOAD DATA LOCAL INFILE '/tmp/propub_metadata.csv'
INTO TABLE Metadata
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 LINES;

# Load the targets

LOAD DATA LOCAL INFILE '/tmp/propub_targets.csv'
INTO TABLE Targets
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 LINES;

CREATE INDEX idx_id ON Entities(id);
CREATE INDEX idx_id ON Messages(id);
CREATE INDEX idx_id ON Metadata(id);
CREATE INDEX idx_id ON Targets(id);

