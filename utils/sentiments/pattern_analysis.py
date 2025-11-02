import pandas as pd
from collections import defaultdict, Counter
from pattern_extractor import extract_filtered_patterns

# ==========================================================
# CARGAR DATASET
# ==========================================================

# Cambia la ruta según tu entorno
df = pd.read_csv("dataset.csv")

# Nos quedamos solo con texto y sentimiento
df = df[["texto", "sentimiento"]]

# Convertimos sentimiento a str por facilidad
df["sentimiento"] = df["sentimiento"].astype(str)


# ==========================================================
# ACUMULAR PATRONES
# ==========================================================

pattern_stats = defaultdict(lambda: {"pos": 0, "neg": 0})

for idx, row in df.iterrows():
    text = row["texto"]
    label = row["sentimiento"]  # "0" = neg, "1" = pos

    patterns = extract_filtered_patterns(text)

    for p in patterns:
        if label == "1":
            pattern_stats[p]["pos"] += 1
        else:
            pattern_stats[p]["neg"] += 1


# ==========================================================
# CONVERTIR A DATAFRAME PARA ANÁLISIS
# ==========================================================

rows = []
for pattern, stats in pattern_stats.items():
    pos = stats["pos"]
    neg = stats["neg"]
    total = pos + neg

    if total == 0:
        continue

    # Polaridad calculada
    polarity_strength = (pos - neg) / total  # → 1 = fuerte positivo, -1 = fuerte negativo

    rows.append({
        "pattern": pattern,
        "pos": pos,
        "neg": neg,
        "total": total,
        "polarity_strength": polarity_strength
    })

patterns_df = pd.DataFrame(rows)

# Ordenar por frecuencia total
top_by_freq = patterns_df.sort_values("total", ascending=False)

# Ordenar por polaridad positiva
top_positive = patterns_df.sort_values("polarity_strength", ascending=False)

# Ordenar por polaridad negativa
top_negative = patterns_df.sort_values("polarity_strength")
