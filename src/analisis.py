"""EDA reproducible para el conjunto Pima Indians Diabetes Database."""
from __future__ import annotations

from pathlib import Path
import sys
import urllib.request

import matplotlib
matplotlib.use("Agg")  # Renderizar archivos sin requerir una ventana gráfica de Tk.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "pima_diabetes.csv"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "figures"
REPORTS = ROOT / "reports"
DATA_URL = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
RAW_COLUMNS = [
    "embarazos", "glucosa_mg_dl", "presion_diastolica_mm_hg",
    "pliegue_tricipital_mm", "insulina_2h_mu_ml", "imc_kg_m2",
    "funcion_antecedentes_diabetes", "edad_anios", "resultado_diabetes",
]
ZERO_MISSING = ["glucosa_mg_dl", "presion_diastolica_mm_hg", "pliegue_tricipital_mm", "insulina_2h_mu_ml", "imc_kg_m2"]
NUMERIC = RAW_COLUMNS[:-1]
LABELS = {0: "No diabetes", 1: "Diabetes"}
COLORS = ["#2463eb", "#e45756", "#12a594", "#f2a541", "#7356bf"]
sns.set_theme(style="whitegrid", palette=COLORS, context="notebook")


def obtain_data() -> pd.DataFrame:
    """Descarga si falta el original y carga sin inferir encabezados."""
    RAW.parent.mkdir(parents=True, exist_ok=True)
    if not RAW.exists() or RAW.stat().st_size == 0:
        print("Descargando CSV público…")
        request = urllib.request.Request(DATA_URL, headers={"User-Agent": "Mozilla/5.0 (academic-eda)"})
        with urllib.request.urlopen(request, timeout=30) as response, RAW.open("wb") as target:
            target.write(response.read())
    df = pd.read_csv(RAW, header=None, names=RAW_COLUMNS)
    if df.shape != (768, 9):
        raise ValueError(f"Se esperaba el CSV clásico de 768×9; se recibió {df.shape}. Revisa la fuente/archivo: {RAW}")
    return df


def prepare_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Audita, tipa, representa ausencias y conserva filas mediante mediana."""
    data = raw.copy()
    audit = {
        "filas_originales": int(len(data)), "columnas_originales": int(data.shape[1]),
        "duplicados_exactos": int(data.duplicated().sum()),
        "nulos_csv": data.isna().sum().astype(int).to_dict(),
        "ceros_sospechosos": {col: int(data[col].eq(0).sum()) for col in ZERO_MISSING},
    }
    for col in RAW_COLUMNS:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    for col in ZERO_MISSING:
        # Los enteros deben pasar a float antes de introducir NaN (Pandas 3.x).
        data[col] = data[col].astype("float64").replace(0, np.nan)
    # Asegura que valores del objetivo inválidos no se conviertan silenciosamente.
    invalid = ~data["resultado_diabetes"].isin([0, 1])
    audit["etiquetas_invalidas"] = int(invalid.sum())
    data.loc[invalid, "resultado_diabetes"] = np.nan
    audit["faltantes_antes_imputacion"] = data.isna().sum().astype(int).to_dict()
    for col in NUMERIC:
        data[col] = data[col].fillna(data[col].median())
    # El objetivo es esencial para análisis por clase: solo filas sin etiqueta se excluyen.
    before = len(data)
    data = data.dropna(subset=["resultado_diabetes"]).copy()
    audit["filas_excluidas_por_objetivo"] = int(before - len(data))
    data["embarazos"] = data["embarazos"].round().astype("int64")
    data["resultado_diabetes"] = data["resultado_diabetes"].astype("int64").map(LABELS).astype("category")
    audit["faltantes_despues"] = data.isna().sum().astype(int).to_dict()
    audit["filas_finales"] = int(len(data))
    audit["columnas_finales"] = int(data.shape[1])
    audit["tipos_finales"] = data.dtypes.astype(str).to_dict()
    return data, audit


def save_univariate(data: pd.DataFrame) -> pd.DataFrame:
    summary = data[NUMERIC].describe().T
    summary["mediana"] = data[NUMERIC].median()
    summary["asimetria"] = data[NUMERIC].skew()
    summary.to_csv(PROCESSED / "resumen_univariado.csv", encoding="utf-8-sig")
    counts = data["resultado_diabetes"].value_counts().rename_axis("clase").to_frame("casos")
    counts["proporcion_pct"] = 100 * counts["casos"] / len(data)
    counts.to_csv(PROCESSED / "frecuencia_resultado.csv", encoding="utf-8-sig")
    ncols = 3
    nrows = int(np.ceil((len(NUMERIC) + 1) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 4.2 * nrows))
    axes = axes.flatten()
    for ax, col in zip(axes, NUMERIC):
        sns.histplot(data=data, x=col, kde=True, color=COLORS[0], ax=ax)
        ax.axvline(data[col].median(), color=COLORS[1], ls="--", lw=1.5, label="Mediana")
        ax.set_title(col.replace("_", " ").title())
        ax.legend(frameon=False)
    sns.countplot(data=data, x="resultado_diabetes", hue="resultado_diabetes", legend=False, ax=axes[-1], palette=COLORS[:2])
    axes[-1].set_title("Casos por resultado")
    axes[-1].set_xlabel("")
    for ax in axes[len(NUMERIC) + 1:]:
        ax.remove()
    fig.suptitle("Análisis univariado: distribución de variables", fontsize=17, y=1.01)
    fig.tight_layout()
    fig.savefig(FIGURES / "01_distribuciones.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return summary


def save_bivariate(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    medians = data.groupby("resultado_diabetes", observed=True)[NUMERIC].median().T
    medians["diferencia_mediana_si_menos_no"] = medians.get("Diabetes") - medians.get("No diabetes")
    medians.to_csv(PROCESSED / "medianas_por_resultado.csv", encoding="utf-8-sig")
    # Fijar sentido de codificación para que coeficientes positivos indiquen
    # asociación con la clase Diabetes (1), no con el orden alfabético de categorías.
    numeric_target = data[NUMERIC].assign(
        resultado_diabetes=data["resultado_diabetes"].astype(str).map({"No diabetes": 0, "Diabetes": 1})
    )
    pearson = numeric_target.corr(method="pearson")["resultado_diabetes"].drop("resultado_diabetes").sort_values(key=abs, ascending=False)
    spearman = numeric_target.corr(method="spearman")["resultado_diabetes"].drop("resultado_diabetes").sort_values(key=abs, ascending=False)
    corr_target = pd.concat([pearson.rename("pearson"), spearman.rename("spearman")], axis=1)
    corr_target.to_csv(PROCESSED / "correlacion_con_resultado.csv", encoding="utf-8-sig")
    fig, axes = plt.subplots(2, 4, figsize=(17, 9))
    for ax, col in zip(axes.flat, NUMERIC):
        sns.boxplot(data=data, x="resultado_diabetes", y=col, hue="resultado_diabetes", legend=False, ax=ax, palette=COLORS[:2], showfliers=True)
        ax.set_title(col.replace("_", " ").title())
        ax.set_xlabel("")
    fig.suptitle("Comparación bivariada: distribuciones por resultado", fontsize=17)
    fig.tight_layout()
    fig.savefig(FIGURES / "02_boxplots_por_resultado.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return medians, corr_target


def save_multivariate(data: pd.DataFrame) -> pd.DataFrame:
    corr = data[NUMERIC].corr(method="pearson")
    corr.to_csv(PROCESSED / "matriz_correlacion_pearson.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(11, 8))
    sns.heatmap(corr, cmap="vlag", center=0, annot=True, fmt=".2f", square=True, linewidths=.5, ax=ax)
    ax.set_title("Matriz de correlación de Pearson — predictores")
    fig.tight_layout()
    fig.savefig(FIGURES / "03_mapa_correlaciones.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    selected = ["glucosa_mg_dl", "imc_kg_m2", "edad_anios", "funcion_antecedentes_diabetes", "resultado_diabetes"]
    pair = data[selected].copy()
    pair["resultado_diabetes"] = pair["resultado_diabetes"].astype(str)
    grid = sns.pairplot(pair, hue="resultado_diabetes", corner=True, diag_kind="hist", plot_kws={"alpha": .45, "s": 20}, palette=COLORS[:2])
    grid.fig.suptitle("Relaciones conjuntas de variables clave", y=1.02)
    grid.savefig(FIGURES / "04_relaciones_conjuntas.png", dpi=160, bbox_inches="tight")
    plt.close(grid.fig)
    x = StandardScaler().fit_transform(data[NUMERIC])
    points = PCA(n_components=2).fit_transform(x)
    pca_data = pd.DataFrame({"componente_1": points[:, 0], "componente_2": points[:, 1], "resultado_diabetes": data["resultado_diabetes"].astype(str)})
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.scatterplot(data=pca_data, x="componente_1", y="componente_2", hue="resultado_diabetes", alpha=.65, s=35, palette=COLORS[:2], ax=ax)
    ax.set_title("PCA exploratorio de predictores estandarizados")
    ax.set_xlabel("Componente principal 1")
    ax.set_ylabel("Componente principal 2")
    fig.tight_layout()
    fig.savefig(FIGURES / "05_pca_exploratorio.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return corr


def iqr_outliers(data: pd.DataFrame) -> pd.Series:
    out = {}
    for col in NUMERIC:
        q1, q3 = data[col].quantile([.25, .75])
        iqr = q3 - q1
        out[col] = int(((data[col] < q1 - 1.5 * iqr) | (data[col] > q3 + 1.5 * iqr)).sum())
    result = pd.Series(out, name="casos_atipicos_regla_iqr")
    result.to_csv(PROCESSED / "conteo_atipicos_iqr.csv", encoding="utf-8-sig")
    return result


def write_report(raw: pd.DataFrame, data: pd.DataFrame, audit: dict, uni: pd.DataFrame, medians: pd.DataFrame, corr_target: pd.DataFrame, corr: pd.DataFrame, outliers: pd.Series) -> None:
    class_share = data["resultado_diabetes"].value_counts(normalize=True) * 100
    top_p = corr_target["pearson"].abs().idxmax()
    top_s = corr_target["spearman"].abs().idxmax()
    pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
    pair_name = pairs.abs().idxmax()
    pair_value = pairs.loc[pair_name]
    zero_text = ", ".join(f"{c}: {n:,}" for c, n in audit["ceros_sospechosos"].items())
    corr_lines = "\n".join(f"| {name} | {row.pearson:.3f} | {row.spearman:.3f} |" for name, row in corr_target.iterrows())
    median_lines = "\n".join(f"| {name} | {row.get('No diabetes', np.nan):.2f} | {row.get('Diabetes', np.nan):.2f} | {row.get('diferencia_mediana_si_menos_no', np.nan):.2f} |" for name, row in medians.iterrows())
    missing_lines = "\n".join(f"| {col} | {num} |" for col, num in audit["faltantes_antes_imputacion"].items() if num)
    if not missing_lines:
        missing_lines = "| No se detectaron | 0 |"
    report = f"""# Informe analítico: Pima Indians Diabetes\n\n## 1. Objetivo\n\nDescribir tendencias y relaciones entre mediciones clínicas y la etiqueta binaria histórica del conjunto. Es un análisis exploratorio de datos agregados y no una herramienta clínica.\n\n## 2. Descripción y procedencia\n\nEl CSV descargado contiene **{len(raw):,} filas y {raw.shape[1]} columnas**. Tras el tratamiento quedan **{len(data):,} registros y {data.shape[1]} variables**. La cohorte se limita a mujeres Pima de al menos 21 años, por lo que los resultados no se deben generalizar sin cautela. La etiqueta expresa inicio de diabetes dentro de cinco años. Véanse las referencias de UCI y Smith et al. en el README.\n\n## 3. Auditoría y limpieza\n\n- Faltantes explícitos del CSV original: **{sum(audit['nulos_csv'].values())}**.\n- Ceros que no son mediciones fisiológicamente válidas y se trataron como ausencia: {zero_text}.\n- Esas ausencias se imputaron con la mediana de cada medición para conservar registros parcialmente útiles. El objetivo no se imputa; filas sin clase válida se excluyen (n={audit['filas_excluidas_por_objetivo']}).\n- Duplicados exactos encontrados: **{audit['duplicados_exactos']}**; se conservaron al no existir ID que permita afirmar que sean errores.\n- Variables tipadas como numéricas, conteo de embarazos entero y resultado como categoría. Nombres normalizados a español y snake_case.\n\n### Faltantes detectados antes de imputar\n\n| Variable | Cantidad |\n|---|---:|\n{missing_lines}\n\n## 4. Análisis univariado\n\nLa clase positiva representa **{class_share.get('Diabetes', 0):.1f}%** (n={int((data['resultado_diabetes']=='Diabetes').sum())}) y la negativa **{class_share.get('No diabetes', 0):.1f}%** (n={int((data['resultado_diabetes']=='No diabetes').sum())}); hay desbalance moderado. Revisar `01_distribuciones.png` y `resumen_univariado.csv` para forma, centro, dispersión y asimetría. La imputación central puede concentrar observaciones alrededor de la mediana, especialmente en insulina y pliegue cutáneo; esto debe tenerse presente al leer histogramas.\n\n## 5. Análisis bivariado\n\nEn los gráficos de caja se comparan medianas y dispersión por clase. Diferencias descriptivas no implican efecto causal ni diagnóstico. La mayor correlación absoluta con la etiqueta codificada es **{top_p}** en Pearson (r={corr_target.loc[top_p, 'pearson']:.3f}) y **{top_s}** en Spearman (rho={corr_target.loc[top_s, 'spearman']:.3f}). Pearson capta relación lineal; Spearman se basa en rangos y responde a relación monótona. La etiqueta binaria hace que estos coeficientes sean asociaciones descriptivas.\n\n| Variable | Pearson con resultado | Spearman con resultado |\n|---|---:|---:|\n{corr_lines}\n\n| Variable | Mediana sin diabetes | Mediana con diabetes | Diferencia (sí − no) |\n|---|---:|---:|---:|\n{median_lines}\n\n## 6. Análisis multivariado y atípicos\n\nEl mayor par de correlación entre predictores es **{pair_name[0]}–{pair_name[1]}** (r={pair_value:.3f}). La matriz completa se incluye en `03_mapa_correlaciones.png`. El pairplot explora distribuciones conjuntas de glucosa, IMC, edad y función de antecedentes; PCA resume variación conjunta luego de estandarizar, pero no se interpreta como separación predictiva.\n\nLa regla IQR marcó observaciones extremas en varias variables. Se conservaron: un punto fuera de 1.5×RIC es candidato a revisión y no prueba error. El boxplot ayuda a distinguir dispersión y extremos en escala original. Conteos completos en `conteo_atipicos_iqr.csv`.\n\n## 7. Conclusiones analíticas\n\n1. La distribución de la clase contiene más resultados negativos que positivos; cualquier modelado posterior debe considerar esta prevalencia y reportar métricas por clase, no solo exactitud.\n2. Glucosa suele mostrar la asociación bivariada más fuerte con el resultado en esta base. Su interpretación es compatible con que sea una medición metabólica informativa, pero la asociación no valida un diagnóstico individual.\n3. El análisis conjunto de edad, IMC, glucosa y antecedentes permite describir perfiles con solapamiento entre clases: no existe una frontera determinista visible en estos gráficos.\n4. Los ceros en cinco mediciones no se interpretan como normalidad fisiológica. Se transformaron en faltantes e imputaron; futuros análisis de sensibilidad deberían comparar imputación por mediana con imputación múltiple o casos completos.\n5. Los extremos, las imputaciones, el tamaño y la selección histórica de la cohorte limitan inferencia y transportabilidad. Se requieren validación externa, contexto clínico y diseño apropiado antes de cualquier uso predictivo.\n\n## 8. Limitaciones\n\nDataset histórico, pequeño frente a bases contemporáneas, cohorte de una población concreta, ausencia de identificadores/tiempo detallado en este CSV y marcadores de ausencia codificados como cero. Correlación no es causalidad; PCA y gráficos son descriptivos. El informe no ofrece consejo médico.\n\n## 9. Figuras y tablas\n\n- `01_distribuciones.png`: histogramas y distribución de clase.\n- `02_boxplots_por_resultado.png`: cajas y bigotes comparados por etiqueta.\n- `03_mapa_correlaciones.png`: matriz Pearson entre predictores.\n- `04_relaciones_conjuntas.png`: pairplot de variables clave.\n- `05_pca_exploratorio.png`: proyección PCA descriptiva.\n- `data/processed/`: tablas CSV con resúmenes y auditoría reutilizables.\n"""
    (REPORTS / "informe_analitico.md").write_text(report, encoding="utf-8")


def main() -> None:
    for path in (PROCESSED, FIGURES, REPORTS):
        path.mkdir(parents=True, exist_ok=True)
    raw = obtain_data()
    clean, audit = prepare_data(raw)
    clean.to_csv(PROCESSED / "diabetes_limpio.csv", index=False, encoding="utf-8-sig")
    pd.Series({k: str(v) for k, v in audit.items() if k not in {"nulos_csv", "ceros_sospechosos", "faltantes_antes_imputacion", "faltantes_despues", "tipos_finales"}}).to_csv(PROCESSED / "auditoria_general.csv", header=["valor"], encoding="utf-8-sig")
    (PROCESSED / "auditoria_detallada.json").write_text(__import__("json").dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    uni = save_univariate(clean)
    medians, corr_target = save_bivariate(clean)
    corr = save_multivariate(clean)
    outliers = iqr_outliers(clean)
    write_report(raw, clean, audit, uni, medians, corr_target, corr, outliers)
    print(f"Listo: {len(clean)} registros limpios. Revisa {REPORTS / 'informe_analitico.md'}")
    print(f"Figuras y tablas guardadas en {ROOT}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise
