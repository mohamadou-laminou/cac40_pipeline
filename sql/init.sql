CREATE TABLE if NOT EXISTS entreprise(
id_entreprise SERIAL PRIMARY KEY,
code_boursier varchar(10) not null UNIQUE,
nom varchar (100) not null,
secteur varchar (100)
);

CREATE TABLE if not exists historique_bourse(
date_jour DATE not null,
id_entreprise integer not null,
prix_fermeture decimal(10 , 2),
volume_echange bigint,
rendement_jour decimal (10 , 4),
volatilite_30 decimal (10, 4),
moyenne_mobile_50 decimal (10 , 2),
FOREIGN KEY (id_entreprise) references entreprise (id_entreprise),
primary key (date_jour, id_entreprise)
);

INSERT INTO entreprise (code_boursier, nom, secteur) VALUES
('MC.PA', 'LVMH', 'Luxe'),
('TTE.PA', 'TotalEnergies', 'Énergie'),
('OR.PA', 'L''Oréal', 'Biens de consommation'),
('RMS.PA', 'Hermès', 'Luxe'),
('SAN.PA', 'Sanofi', 'Santé'),
('AIR.PA', 'Airbus', 'Industrie'),
('SU.PA', 'Schneider Electric', 'Industrie'),
('AI.PA', 'Air Liquide', 'Matériaux'),
('DG.PA', 'Vinci', 'BTP'),
('BNP.PA', 'BNP Paribas', 'Finance')
ON CONFLICT (code_boursier) DO NOTHING;