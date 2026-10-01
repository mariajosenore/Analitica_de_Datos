# Análisis exploratorio de diabetes — Pima Indians

Proyecto académico reproducible en Python. Realiza auditoría de calidad, limpieza documentada y análisis exploratorio univariado, bivariado y multivariado. El foco es describir asociaciones en los datos; no diagnostica ni demuestra causalidad.

## Dataset y alcance

Se usa el conjunto **Pima Indians Diabetes Database**: 768 observaciones, 8 variables explicativas y una etiqueta binaria (`Outcome`), es decir, 9 columnas. Los registros corresponden a mujeres de herencia Pima de 21 años o más. La etiqueta significa inicio de diabetes dentro de cinco años según la definición histórica del conjunto. No representa población general ni reemplaza evaluación clínica.

La ficha de UCI registra la base y su identificador DOI [10.24432/C5T59G](https://doi.org/10.24432/C5T59G); la descripción clásica atribuye la recolección al NIDDK y documenta las variables, población y artículo de Smith et al. (1988) [documentación CRAN del conjunto](https://search.r-project.org/CRAN/refmans/reglogit/html/pima.html). Una copia CSV reproducible se obtiene del [espejo público de datos de Brownlee](https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv), cuyas 768 líneas fueron verificadas al preparar este proyecto. El archivo no lleva encabezados; el código los asigna según el diccionario clásico.

## Estructura

```text
analisis_diabetes/
├── data/
│   ├── raw/                  # CSV original descargado
│   └── processed/            # CSV limpio, valores ausentes en blanco
├── figures/                  # PNG: distribución, boxplots, correlaciones y multivariado
├── reports/                  # informe generado con resultados numéricos observados
├── src/analisis.py           # flujo reproducible de principio a fin
├── notebooks/analisis_diabetes.ipynb
├── requirements.txt
└── README.md
```

## Reproducir en Visual Studio Code

1. Abre `analisis_diabetes.code-workspace` en VS Code (o abre esta carpeta del proyecto, no solamente `src/`).
2. Instala Python 3.10 o posterior y selecciona el intérprete.
3. El workspace indica a VS Code que use el intérprete de `.venv`. Si Pylance aún muestra imports sin resolver, usa `Ctrl+Shift+P` → **Python: Select Interpreter** → **Enter interpreter path** y selecciona `<carpeta del proyecto>\\.venv\\Scripts\\python.exe`; después ejecuta **Developer: Reload Window**.
4. Abre Terminal → Nueva terminal y ejecuta:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python src/analisis.py
   ```

   Si la política de PowerShell bloquea la activación, ejecuta el script con `\.venv\Scripts\python.exe src\analisis.py`.
5. El CSV original ya viene en `data/raw/`. Si se elimina, la primera ejecución lo descarga de la fuente pública. Después de ejecutar, revisa `reports/informe_analitico.md`, `data/processed/diabetes_limpio.csv` y las figuras.
6. Para trabajar paso a paso, abre `notebooks/analisis_diabetes.ipynb`, selecciona el mismo `.venv` como kernel y ejecuta las celdas de arriba abajo. El notebook llama las mismas funciones de `src/analisis.py`, evitando duplicar lógica.

## Decisiones de calidad y limpieza

* **Nulos explícitos:** primero se cuentan los `NaN` tal como vienen. El archivo clásico normalmente los representa como ceros en cinco mediciones: `glucosa_mg_dl`, `presion_diastolica_mm_hg`, `pliegue_tricipital_mm`, `insulina_2h_mu_ml` e `imc_kg_m2`. Cero es fisiológicamente inválido para esas mediciones, así que se convierte a `NaN`, sin borrar la fila. Se conservan los registros para no perder información válida del resto de columnas y se imputan faltantes con la mediana de la propia variable, una medida robusta ante asimetría y valores extremos. El informe muestra la cantidad inicial y final por variable.
* **No se reemplazan por cero** mediciones faltantes: eso sesgaría promedios, correlaciones y gráficos hacia valores imposibles.
* **Conversión de tipo:** todas las columnas pasan a tipo numérico; `embarazos` se conserva entero; `resultado_diabetes` se convierte a categoría etiquetada No/Sí. Cualquier valor no interpretable se cuenta como faltante antes de imputar.
* **Nombres normalizados:** minúsculas, snake_case, español y unidades cuando aplica. `resultado_diabetes` se reserva para el objetivo.
* **Duplicados:** se informan; no se eliminan automáticamente porque dos personas pueden compartir las mismas mediciones y el dataset no ofrece un identificador que pruebe que una fila sea una repetición.
* **Atípicos:** se señalan por regla IQR en caja y bigotes, no se borran automáticamente. Un extremo estadístico puede ser clínicamente plausible y requiere contexto.
* **Normalización de escala:** no se escalan valores para la EDA, porque unidades originales son interpretables. Si se necesitara un modelo, la estandarización debe ajustarse solo sobre datos de entrenamiento para evitar fuga de información.

## Qué análisis incluye

* **Univariado:** conteos, media, mediana, desviación, cuartiles, asimetría y histogramas por variable; frecuencia y proporción del resultado.
* **Bivariado:** distribución numérica por estado de diabetes con boxplots; comparación de medianas; correlación de Pearson y Spearman con `resultado_diabetes` codificado 0/1. Ambas describen asociación, no causa.
* **Multivariado:** mapa de calor de Pearson, pairplot de variables clave con color por clase y PCA exploratorio de variables numéricas estandarizadas. PCA visualiza variación conjunta y no es un clasificador.
* **Extremos:** regla de Tukey (`Q1 − 1.5×RIC`, `Q3 + 1.5×RIC`) y conteo por atributo antes/después de la imputación.
* **Conclusiones automáticas:** el informe generado redacta tendencias con los valores efectivamente calculados, incluyendo limitaciones y advertencias interpretativas.

## Archivos generados

`python src/analisis.py` crea el dataset limpio, tablas CSV auxiliares, figuras PNG e informe analítico. No se hacen pruebas clínicas ni se recomienda usar este análisis para decisiones individuales.

## Referencias

1. UCI Machine Learning Repository, *Pima Indians Diabetes Database*, DOI: [10.24432/C5T59G](https://doi.org/10.24432/C5T59G).
2. Smith, J. W., Everhart, J. E., Dickson, W. C., Knowler, W. C. & Johannes, R. S. (1988). “Using the ADAP learning algorithm to forecast the onset of diabetes mellitus”. *Proceedings of the Symposium on Computer Applications in Medical Care*, 261–265.
3. Brownlee, J., espejo público del CSV: [pima-indians-diabetes.data.csv](https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv).
