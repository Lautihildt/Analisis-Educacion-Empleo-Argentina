# 🇦🇷 Analysis of Productive Matrix and Educational Supply in Argentina

### A Data Science approach to territorial inequalities and structural gaps.

This project analyzes the relationship between educational infrastructure and labor demand in Argentina using official 2022 data. Through a data engineering pipeline and geospatial analysis, the study aims to answer: **Does the supply of schools align with labor demand across the country?**

---

## 🚀 Executive Summary
The analysis integrated heterogeneous sources (Population Census, Educational Institution Registry, and Employment Records) to identify distribution patterns. A structural divergence was detected: while education has **high territorial capillarity** (reaching all regions), the labor market exhibits **extreme centralization** in the country's "core zone."

## 📊 Key Findings and Visualizations

### 1. Employment Centralization vs. Educational Distribution
The most significant contrast in the analysis.
* **Employment Map:** A clear "Productive Corridor" is observed (Buenos Aires, Santa Fe, Córdoba). Outside this axis, "productive deserts" are identified.
* **Education Map:** School infrastructure is much more homogeneous, acting as a demographic anchor even where the private labor market is scarce.

> **Note:** Insert your map images here using: 
> `![Employment Map](path_to_your_image/mapa_geo_empleados.png)`

### 2. Gender Gap: "Glass Walls"
By analyzing productive sectors (CLAE), we confirmed horizontal segregation.
* **Female-Dominated Sectors:** Education and Healthcare exceed 70% female participation.
* **Male-Dominated Sectors:** Construction, Transport, and Agribusiness show participation below 15%, limiting women's access to high-income sectors.

### 3. Lack of Linear Correlation
The data suggests that **educational supply responds to demographics, not to the labor market**. When normalized by population, there is no direct correlation ($R^2$ is low) between school density and per capita employment generation at the departmental level.

---

## ⚙️ Data Engineering & Methodology

The project simulates a real-world Data Engineering workflow:

1.  **ETL & Cleaning (Pandas):**
    * Normalization of government datasets (handling inconsistent CSV/Excel formats).
    * Standardization of geographic codes (INDEC vs. local names) and management of inconsistencies in department IDs.
2.  **Data Modeling:**
    * Design of a normalized relational schema up to **Third Normal Form (3NF)** to ensure data integrity.
3.  **Data Quality (GQM):**
    * Application of the **Goal-Question-Metric** methodology to audit quality, quantifying error rates in geolocation.
4.  **Advanced SQL Analysis (DuckDB):**
    * Use of SQL embedded in Python for complex aggregations and rankings.

## 🧠 SQL Showcase (DuckDB)
The analysis utilized **Window Functions** and **CTEs**. Example query to rank productive efficiency by province:

```sql
SELECT 
    d.Provincia_Nombre,
    d.Departamento_Nombre,
    p.Cant_Empresas_Exportadoras,
    RANK() OVER (PARTITION BY d.Provincia_Nombre ORDER BY p.Cant_Empresas_Exportadoras DESC) as Provincial_Ranking
FROM departamentos_info d
JOIN establecimientos_productivos p ON d.Departamento_Id = p.Departamento_Id
WHERE p.Cant_Empresas_Exportadoras > 10;
