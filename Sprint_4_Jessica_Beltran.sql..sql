NIVELL 1

Exercici 1

Consulta sobre Taula no Optimitzada (Diagnòstic)

Codi SQL:

SELECT 
  c.country,
  DATE(t.timestamp),
  t.transaction_id,
  t.amount,
FROM `sprint3_silver.transactions_clean` AS t
INNER JOIN `sprint3_silver.companies_clean` AS c
  ON t.business_id = c.company_id
WHERE c.country = 'Germany' AND
  DATE(t.timestamp) = '2022-03-12'
  ORDER BY t.amount DESC;

Exercici 2

Re-arquitectura i Optimització de l'Emmagatzematge (Partition & Cluster)

 Pas 1, creció nova taula:

CREATE OR REPLACE TABLE proverbial-deck-498507-c9.sprint3_silver.transactions_recent AS
  SELECT * EXCEPT(timestamp),
   TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL CAST(RAND() * 50 AS INT64) DAY)       
   AS timestamp 
FROM proverbial-deck-498507-c9.sprint3_silver.transactions_clean;

Pas 2, creació de taula particionada i clusteritzada:

CREATE OR REPLACE TABLE proverbial-deck-498507-c9.sprint3_gold.fact_transactions_optimized
PARTITION BY DATE(timestamp)
CLUSTER BY business_id
  AS SELECT * FROM
  proverbial-deck-498507-c9.sprint3_silver.transactions_recent;

Exercici 3

La Prova del Cotó (Benchmark)

Codi per la comparativa de les consultes amb la taula optimitzada i la no optimitzada:

-- Consulta amb la taula no optimitzada

SELECT 
* FROM
proverbial-deck-498507-c9.sprint3_silver.transactions_recent
WHERE
DATE(timestamp)>=DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)

-- Consulta amb la taula optimitzada

SELECT 
* FROM
proverbial-deck-498507-c9.sprint3_gold.fact_transactions_optimized
WHERE
DATE(timestamp)>=DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)

Exercici 4

Smart Caching (Vistes Materialitzades)

Codi per la creació de la vista materialitzada:


CREATE MATERIALIZED VIEW proverbial-deck-498507-c9.sprint3_gold.mv_daily_sales
OPTIONS (
  enable_refresh = true
)
AS
SELECT
  DATE(t.timestamp) AS date_of_sales,
  ROUND(SUM(IF(t.declined = 0, t.amount, 0)), 2) AS total_sales,
  COUNT(IF(t.declined = 0, t.transaction_id, NULL)) AS num_transactions
FROM
  proverbial-deck-498507-c9.sprint3_gold.fact_transactions_optimized AS t
GROUP BY
  DATE(t.timestamp);

Afegim una altre consulta per fer el ROUND:

SELECT 
  date_of_sales,
  ROUND(total_sales, 2) AS total_sales,
  num_transactions
FROM sprint3_gold.mv_daily_sales

  Codi per consultar la vista materialitzada:

SELECT *
FROM proverbial-deck-498507-c9.sprint3_gold.mv_daily_sales
WHERE date_of_sales = CURRENT_DATE();

NIVELL 2

Exercici 1

Perfilat de Clients VIP (Mètriques Agregades amb CTEs

Codi per crear la CTE i calcular les mètriques per al perfilat de clients VIP:

WITH VIP_Stats AS (
  SELECT 
    t.user_id,
    ROUND(SUM(t.amount), 2) AS total_amount,
    COUNT(DISTINCT t.transaction_id) AS num_transactions,
    ROUND(AVG(t.amount), 2) AS ticket_average,
    MAX(t.amount) AS max_amount
  FROM proverbial-deck-498507-c9.sprint3_gold.fact_transactions_optimized AS t
  GROUP BY t.user_id
  HAVING total_amount > 500
)

SELECT
  u.user_id,
  CONCAT(u.name,' ',u.surname) AS name,
  u.email,
  v.total_amount,
  v.max_amount,
  v.ticket_average,
  v.num_transactions
FROM VIP_stats AS v
JOIN proverbial-deck-498507-c9.sprint3_silver.users_combined AS u
  ON v.user_id = u.user_id
ORDER BY total_amount DESC;

Exercici 2

Anàlisi de Tendències (Window Functions sobre Vistes)


Codi per crear la vista amb les vendes diàries i les tendències:

SELECT 
 date_of_sales, 
 ROUND(total_sales, 2) AS today_sales,
 ROUND(LAG(total_sales) OVER (ORDER BY date_of_sales), 2) AS yesterday_sales,
 ROUND(
  (total_sales - LAG(total_sales) OVER (ORDER BY date_of_sales))
 / NULLIF(LAG(total_sales) OVER (ORDER BY date_of_sales), 0) *100
 ,2) AS Diff_percentual
FROM proverbial-deck-498507-c9.sprint3_gold.mv_daily_sales
ORDER BY date_of_sales ASC;


Exercici 3

Totals Acumulats (Running Totals sobre Vistes)

Codi per calcular els totals acumulats de vendes:

SELECT
  date_of_sales,
  ROUND(total_sales, 2) AS total_sales,
  ROUND(
  SUM(total_sales) OVER (
   PARTITION BY EXTRACT(YEAR FROM date_of_sales)
   ORDER BY date_of_sales
   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW 
  ) 
  , 2) AS ytd_sales
  FROM proverbial-deck-498507-c9.sprint3_gold.mv_daily_sales
  ORDER BY date_of_sales;


Exercici 4

Fidelització i Valor del Client (Filtratge Avançat)

Codi per identificar els clients que han realitzat almenys 3 compres i calcular la mitjana de les seves 3 primeres compres:

SELECT 
 u.user_id,
 CONCAT(u.name,' ',u.surname) AS name,
 u.email,
 t.timestamp AS date_of_sale,
 t.amount,
 ROUND(
  AVG(t.amount) OVER (
   PARTITION BY t.user_id
   ORDER BY t.timestamp
   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW 
  )
 , 2) AS avg_3_sales,
  
 ROW_NUMBER() OVER (PARTITION BY t.user_id ORDER BY t.timestamp) AS row_num

FROM proverbial-deck-498507-c9.sprint3_silver.transactions_clean AS t
INNER JOIN proverbial-deck-498507-c9.sprint3_silver.users_combined AS u
 ON t.user_id = u.user_id
WHERE t.declined = 0
QUALIFY row_num = 3
ORDER BY avg_3_sales DESC;


NIVELL 3

Exercici 1 

Desanidament i Aplanament de Dades (Unnesting)

Codi per desanidar i aplanar les dades:

CREATE OR REPLACE TABLE proverbial-deck-498507-c9.sprint3_gold.dim_transactions_flat AS
SELECT
  t.transaction_id,
  DATE (t.timestamp) AS transaction_date,
  t.amount AS total_ticket,
  p.product_id AS product_sku,
  p.name AS product_name,
  p.price AS product_price
FROM 
 proverbial-deck-498507-c9.sprint3_gold.fact_transactions_optimized AS t
CROSS JOIN UNNEST(t.product_ids) AS product_sku
INNER JOIN
 proverbial-deck-498507-c9.sprint3_silver.products_clean AS p
ON product_sku = p.product_id;



Exercici 2

El Rànquing de Vendes (Agregació Simple)

Codi per calcular el rànquing de vendes per producte:

SELECT  
product_name,
product_price,
product_sku,
COUNT(*) AS total_sold
FROM
proverbial-deck-498507-c9.sprint3_gold.dim_transactions_flat
GROUP BY product_name,product_sku,product_price
ORDER BY total_sold DESC LIMIT 5;

Exercici 3

Automatització del Pipeline i Visualització

Codif per la UDF :

CREATE OR REPLACE FUNCTION sprint3_gold.calculate_tax(amount FLOAT64)
RETURNS FLOAT64
AS (
  ROUND(amount * 1.21, 2)
);

CREATE OR REPLACE TABLE sprint3_gold.dim_transactions_flat AS
SELECT
  t.transaction_id,
  DATE(t.timestamp) AS transaction_date,
  t.amount AS total_ticket,
  p.product_id AS product_sku,
  p.name AS product_name,
  p.price AS product_price, 
  sprint3_gold.calculate_tax(p.price) AS tax_included_price
FROM 
 sprint3_gold.fact_transactions_optimized AS t 
CROSS JOIN UNNEST(t.product_ids) AS product_sku
INNER JOIN
 sprint3_silver.products_clean AS p 
ON product_sku = p.product_id;

Enllaç dashboard Looker Studio:

https://datastudio.google.com/s/t67dEvkiXcQ

