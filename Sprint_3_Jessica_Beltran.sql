NIVELL 1

Exercici 1

Entorn i Ingesta Hibrida (Code-First)

Creem el dataset Bronze pe la interfície gràfica de BigQuery UI


Codi per crear dataset Silver:

CREATE SCHEMA `proverbial-deck-498507-c9.sprint3_silver`
OPTIONS(
  location = 'EU'
);

Comanda de Cloud per al dataset Gold:

bq mk --data_location=EU proverbial-deck-498507-c9:sprint3_gold

Exercici 2 

Codi per a la taula transactions_raw:

CREATE OR REPLACE EXTERNAL TABLE `proverbial-deck-498507-c9.sprint3_bronze.transactions_raw`
OPTIONS (
  format = 'CSV',
  uris = ['gs://sprint3-data-lake-jessica/transactions.csv'],
  skip_leading_rows = 1,
  field_delimiter = ','
);

Codi per a la taula companies_raw:

CREATE OR REPLACE EXTERNAL TABLE `proverbial-deck-498507-c9.sprint3_bronze.companies_raw` (
  company_id STRING,
  company_name STRING,
  phone STRING,
  email STRING,
  country STRING,
  website STRING,
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://bootcamp-data-analytics-public/ERP/companies.csv'],
  skip_leading_rows = 1,
  field_delimiter = ','
);

Codi per a la taula european_users_raw:

CREATE OR REPLACE EXTERNAL TABLE `proverbial-deck-498507-c9.sprint3_bronze.european_users_raw`
OPTIONS (
  format = 'CSV',
  uris = ['gs://bootcamp-data-analytics-public/CRM/european_users.csv'],
  skip_leading_rows = 1,
  field_delimiter = ','
);
Codi per a la taula american_users_raw:

CREATE OR REPLACE EXTERNAL TABLE `proverbial-deck-498507-c9.sprint3_bronze.american_users_raw`
OPTIONS (
  format = 'CSV',
  uris = ['gs://bootcamp-data-analytics-public/CRM/american_users.csv'],
  skip_leading_rows = 1,
  field_delimiter = ','
);

Codi per a la taula credit_cards_raw:

CREATE OR REPLACE EXTERNAL TABLE `proverbial-deck-498507-c9.sprint3_bronze.credit_cards_raw`
OPTIONS (
  format = 'CSV',
  uris = ['gs://bootcamp-data-analytics-public/CRM/credit_cards.csv'],
  skip_leading_rows = 1,
  field_delimiter = ','
);

Exercici 3

Càrrega de Dades Locals (Upload)

Pujada d'arxiu CSV manual i la creem com a taula nativa a BigQuery

Exercici 4

Arquitectura i Rendiment. Materialització de Dades (Assistit per IA)

Prompt per a la materialització de dades:

Write a SQL query to create a new table called transactions_raw_native in the sprint3_bronze dataset. 
It should contain all data from the transactions_raw table. 
Please use CREATE OR REPLACE TABLE so I don't get errors if I run it more than once.

Codi per a la taula transactions_raw_native:

CREATE OR REPLACE TABLE `proverbial-deck-498507-c9.sprint3_bronze.transactions_raw_native` AS
SELECT * FROM `proverbial-deck-498507-c9.sprint3_bronze.transactions_raw`;

Auditoria de costos:

SELECT id FROM `proverbial-deck-498507-c9.sprint3_bronze.transactions_raw`

SELECT id FROM `proverbial-deck-498507-c9.sprint3_bronze.transactions_raw_native`

El perill del LIMIT:

SELECT * FROM `proverbial-deck-498507-c9.sprint3_bronze.transactions` LIMIT 10;

SELECT * FROM `proverbial-deck-498507-c9.sprint3_bronze.transactions`;

Exercici 5

Adaptació de Sintaxi (Reporting)

Codi per a la consulta de transaccions amb sintaxi adaptada:

SELECT 
  EXTRACT(DATE FROM timestamp) AS data_transaccions,
  ROUND(SUM(amount), 2) AS total
FROM 
  `proverbial-deck-498507-c9.sprint3_bronze.transactions_raw_native`
WHERE 
  EXTRACT(YEAR FROM timestamp) = 2021
GROUP BY 
  data_transaccions
ORDER BY 
  total DESC
LIMIT 5;

Exercici 6

Consultes Complexes

Codi per l'informe que creui dades entre transaccions i companyies:

SELECT
    c.company_name,
    c.country,
    DATE(t.timestamp) AS transaction_date
FROM
    `proverbial-deck-498507-c9.sprint3_bronze.companies_raw` AS c
INNER JOIN
    `proverbial-deck-498507-c9.sprint3_bronze.transactions_raw_native` AS t
    ON c.company_id = t.business_id
WHERE
    t.declined = 0
    AND t.amount BETWEEN 100 AND 200 
    AND DATE(t.timestamp) IN ('2015-04-29', '2018-07-20', '2024-03-13')
ORDER BY 
    transaction_date DESC;


NIVELL 2

Exercici 1

Neteja de productes (Data Quality)

Codi per la nova taula de productes neta (sprint3_silver.products_clean):

CREATE OR REPLACE TABLE proverbial-deck-498507-c9.sprint3_silver.products_clean AS
SELECT
 id AS product_id,
 product_name AS name,
CAST(REPLACE(warehouse_id, 'WH-', '') AS INT64) AS warehouse_id,
CAST(price as FLOAT64) AS price,
weight,
colour,
category,
brand,
cost,
launch_date
FROM
proverbial-deck-498507-c9.sprint3_bronze.products_raw;
 
 Exercici 2

Creació de Transaccions netes (Capa Silver)

Codi per la nova taula de transaccions neta (sprint3_silver.transactions_clean):

 CREATE OR REPLACE TABLE proverbial-deck-498507-c9.sprint3_silver.transactions_clean AS
SELECT
    id AS transaction_id,
    IFNULL(SAFE_CAST(amount AS FLOAT64), 0) AS amount,
    timestamp,
    SAFE_CAST(lat AS FLOAT64) AS lat,
    SAFE_CAST(longitude AS FLOAT64) AS longitude,
ARRAY(
      SELECT CAST(id_text AS INT64)
      FROM UNNEST(SPLIT(product_ids, ',')) AS id_text
    ) AS product_ids,
    user_id,
    card_id,
    business_id,
    declined
FROM
    proverbial-deck-498507-c9.sprint3_bronze.transactions_raw;

Exercici 3

Unificació d'usuaris (UNION)

Codi per a la nova tauda d'usuaris unificada (sprint3_silver.users_combined):

CREATE  OR REPLACE TABLE proverbial-deck-498507-c9.sprint3_silver.users_combined AS
SELECT
  id AS user_id,
  * EXCEPT(id),
  'USA' AS origin,
  FROM
  proverbial-deck-498507-c9.sprint3_bronze.american_users_raw

  UNION ALL 

  SELECT
  id AS user_id,
  * EXCEPT(id),
  'EU' AS origin,
  FROM
  proverbial-deck-498507-c9.sprint3_bronze.european_users_raw;

Exercici 4

Materialització de Companyies i Targetes de Crèdit 

Codi per a la nova taula de credit_cards (sprint3_silver.credit_cards):

CREATE OR REPLACE TABLE proverbial-deck-498507-c9.sprint3_silver.credit_cards_clean AS
SELECT 
 id AS card_id,
 user_id,
 iban,
 pan,
 cvv,
 track1,
 track2,
 expiring_date FROM
  proverbial-deck-498507-c9.sprint3_bronze.credit_cards_raw;


Codi per a la nova taula de companies (sprint3_silver.companies):

CREATE OR REPLACE TABLE proverbial-deck-498507-c9.sprint3_silver.companies_clean AS
SELECT * FROM
  proverbial-deck-498507-c9.sprint3_bronze.companies_raw;


NIVELL 3

Exercici 1

Presentació de Dades i Creació de Vistes

Codi per a la vista v_marketing_kpis (sprint3_gold.v_marketing_kpis):

CREATE OR REPLACE VIEW proverbial-deck-498507-c9.sprint3_gold.v_marketing_kpis AS
SELECT
  c.company_name,
  c.phone,
  c.country,
  ROUND(AVG(t.amount), 2) AS average_amount,
CASE 
  WHEN AVG(t.amount) > 260 THEN 'Premium'
  ELSE 'Standard'
END AS client_tier
FROM proverbial-deck-498507-c9.sprint3_silver.companies_clean AS c
LEFT JOIN proverbial-deck-498507-c9.sprint3_silver.transactions_clean AS t
ON c.company_id = t.business_id
GROUP BY c.company_name, c.phone, c.country;

Codi per a la visualització de la vista v_marketing_kpis:

SELECT * FROM `proverbial-deck-498507-c9.sprint3_gold.v_marketing_kpis`
ORDER BY 
  client_tier DESC, 
  average_amount DESC;

Exercici 2

Rànquing de Productes (La Potència dels Arrays)

Codi per a la vista v_product_ranking (sprint3_gold.v_product_ranking):

CREATE OR REPLACE TABLE proverbial-deck-498507-c9.sprint3_gold.product_sales_ranking AS
SELECT 
  p.product_id,
  p.name,
  p.price,
  p.colour,
  COUNT(t.transaction_id) AS total_sold
FROM proverbial-deck-498507-c9.sprint3_silver.products_clean AS p
LEFT JOIN proverbial-deck-498507-c9.sprint3_silver.transactions_clean AS t
  ON p.product_id IN UNNEST(t.product_ids)
GROUP BY 
  p.product_id, 
  p.name, 
  p.price, 
  p.colour
ORDER BY 
  total_sold DESC;


Exercici 3

Exportació de Resultats a Google Sheets o Excel

codi per a exportar la vista v_product_ranking a Google Sheets:

SELECT * FROM proverbial-deck-498507-c9.sprint3_gold.product_sales_ranking;


  


