# Informe analítico: Pima Indians Diabetes

## 1. Objetivo

Describir tendencias y relaciones entre mediciones clínicas y la etiqueta binaria histórica del conjunto. Es un análisis exploratorio de datos agregados y no una herramienta clínica.

## 2. Descripción y procedencia

El CSV descargado contiene **768 filas y 9 columnas**. Tras el tratamiento quedan **768 registros y 9 variables**. La cohorte se limita a mujeres Pima de al menos 21 años, por lo que los resultados no se deben generalizar sin cautela. La etiqueta expresa inicio de diabetes dentro de cinco años. Véanse las referencias de UCI y Smith et al. en el README.

## 3. Auditoría y limpieza

- Faltantes explícitos del CSV original: **0**.
- Ceros que no son mediciones fisiológicamente válidas y se trataron como ausencia: glucosa_mg_dl: 5, presion_diastolica_mm_hg: 35, pliegue_tricipital_mm: 227, insulina_2h_mu_ml: 374, imc_kg_m2: 11.
- Esas ausencias se imputaron con la mediana de cada medición para conservar registros parcialmente útiles. El objetivo no se imputa; filas sin clase válida se excluyen (n=0).
- Duplicados exactos encontrados: **0**; se conservaron al no existir ID que permita afirmar que sean errores.
- Variables tipadas como numéricas, conteo de embarazos entero y resultado como categoría. Nombres normalizados a español y snake_case.

### Faltantes detectados antes de imputar

| Variable | Cantidad |
|---|---:|
| glucosa_mg_dl | 5 |
| presion_diastolica_mm_hg | 35 |
| pliegue_tricipital_mm | 227 |
| insulina_2h_mu_ml | 374 |
| imc_kg_m2 | 11 |

## 4. Análisis univariado

La clase positiva representa **34.9%** (n=268) y la negativa **65.1%** (n=500); hay desbalance moderado. Revisar `01_distribuciones.png` y `resumen_univariado.csv` para forma, centro, dispersión y asimetría. La imputación central puede concentrar observaciones alrededor de la mediana, especialmente en insulina y pliegue cutáneo; esto debe tenerse presente al leer histogramas.

## 5. Análisis bivariado

En los gráficos de caja se comparan medianas y dispersión por clase. Diferencias descriptivas no implican efecto causal ni diagnóstico. La mayor correlación absoluta con la etiqueta codificada es **glucosa_mg_dl** en Pearson (r=0.493) y **glucosa_mg_dl** en Spearman (rho=0.481). Pearson capta relación lineal; Spearman se basa en rangos y responde a relación monótona. La etiqueta binaria hace que estos coeficientes sean asociaciones descriptivas.

| Variable | Pearson con resultado | Spearman con resultado |
|---|---:|---:|
| glucosa_mg_dl | 0.493 | 0.481 |
| imc_kg_m2 | 0.312 | 0.307 |
| edad_anios | 0.238 | 0.309 |
| embarazos | 0.222 | 0.199 |
| pliegue_tricipital_mm | 0.215 | 0.216 |
| insulina_2h_mu_ml | 0.204 | 0.274 |
| funcion_antecedentes_diabetes | 0.174 | 0.175 |
| presion_diastolica_mm_hg | 0.166 | 0.171 |

| Variable | Mediana sin diabetes | Mediana con diabetes | Diferencia (sí − no) |
|---|---:|---:|---:|
| embarazos | 2.00 | 4.00 | 2.00 |
| glucosa_mg_dl | 107.50 | 140.00 | 32.50 |
| presion_diastolica_mm_hg | 72.00 | 74.00 | 2.00 |
| pliegue_tricipital_mm | 29.00 | 29.00 | 0.00 |
| insulina_2h_mu_ml | 125.00 | 125.00 | 0.00 |
| imc_kg_m2 | 30.40 | 34.25 | 3.85 |
| funcion_antecedentes_diabetes | 0.34 | 0.45 | 0.11 |
| edad_anios | 27.00 | 36.00 | 9.00 |

## 6. Análisis multivariado y atípicos

El mayor par de correlación entre predictores es **embarazos–edad_anios** (r=0.544). La matriz completa se incluye en `03_mapa_correlaciones.png`. El pairplot explora distribuciones conjuntas de glucosa, IMC, edad y función de antecedentes; PCA resume variación conjunta luego de estandarizar, pero no se interpreta como separación predictiva.

La regla IQR marcó observaciones extremas en varias variables. Se conservaron: un punto fuera de 1.5×RIC es candidato a revisión y no prueba error. El boxplot ayuda a distinguir dispersión y extremos en escala original. Conteos completos en `conteo_atipicos_iqr.csv`.

## 7. Conclusiones analíticas

1. La distribución de la clase contiene más resultados negativos que positivos; cualquier modelado posterior debe considerar esta prevalencia y reportar métricas por clase, no solo exactitud.
2. Glucosa suele mostrar la asociación bivariada más fuerte con el resultado en esta base. Su interpretación es compatible con que sea una medición metabólica informativa, pero la asociación no valida un diagnóstico individual.
3. El análisis conjunto de edad, IMC, glucosa y antecedentes permite describir perfiles con solapamiento entre clases: no existe una frontera determinista visible en estos gráficos.
4. Los ceros en cinco mediciones no se interpretan como normalidad fisiológica. Se transformaron en faltantes e imputaron; futuros análisis de sensibilidad deberían comparar imputación por mediana con imputación múltiple o casos completos.
5. Los extremos, las imputaciones, el tamaño y la selección histórica de la cohorte limitan inferencia y transportabilidad. Se requieren validación externa, contexto clínico y diseño apropiado antes de cualquier uso predictivo.

## 8. Limitaciones

Dataset histórico, pequeño frente a bases contemporáneas, cohorte de una población concreta, ausencia de identificadores/tiempo detallado en este CSV y marcadores de ausencia codificados como cero. Correlación no es causalidad; PCA y gráficos son descriptivos. El informe no ofrece consejo médico.

## 9. Figuras y tablas

- `01_distribuciones.png`: histogramas y distribución de clase.
- `02_boxplots_por_resultado.png`: cajas y bigotes comparados por etiqueta.
- `03_mapa_correlaciones.png`: matriz Pearson entre predictores.
- `04_relaciones_conjuntas.png`: pairplot de variables clave.
- `05_pca_exploratorio.png`: proyección PCA descriptiva.
- `data/processed/`: tablas CSV con resúmenes y auditoría reutilizables.
