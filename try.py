import pandas as pd, numpy as np, matplotlib.pyplot as plt, os
from caas_jupyter_tools import display_dataframe_to_user

path = "/mnt/data/cleaned_bank_data.csv"
df = pd.read_csv(path)

# ---------- Step 1: Dataset       Overview ----------
overview = pd.DataFrame(
    {
        "column": df.columns,
        "dtype": [str(t) for t in df.dtypes],
        "non_null": df.notna().sum().values,
        "missing_%": (df.isna().mean() * 100).round(2).values,
        "n_unique": df.nunique(dropna=True).values,
    }
)
samples = []
for c in df.columns:
    vals = df[c].dropna().unique()
    samples.append(", ".join([str(v)[:22] for v in vals[:5]]))
overview["sample_values"] = samples
display_dataframe_to_user("Dataset Overview (raw)", overview)
display_dataframe_to_user("First 5 rows (raw)", df.head(5))

# ---------- Step 2: Data Quality Summary ----------
# Duplicate columns check (exact)
dup_cols = []
cols = list(df.columns)
for i, c1 in enumerate(cols):
    for c2 in cols[i + 1 :]:
        try:
            if df[c1].equals(df[c2]):
                dup_cols.append((c1, c2))
        except Exception:
            pass
dup_cols_df = pd.DataFrame(dup_cols, columns=["col_a", "col_b"])
display_dataframe_to_user(
    "Exact duplicate columns detected",
    dup_cols_df if len(dup_cols_df) else pd.DataFrame({"note": ["None detected"]}),
)

dupe_rows = df.duplicated().sum()
dupe_customer = (
    df.duplicated(subset=["CustomerId"]).sum() if "CustomerId" in df.columns else np.nan
)
dq = pd.DataFrame(
    {
        "metric": [
            "rows",
            "columns",
            "duplicate_rows_full",
            "duplicate_customerid_rows",
        ],
        "value": [len(df), df.shape[1], dupe_rows, dupe_customer],
    }
)
display_dataframe_to_user("Data Quality Summary (basic)", dq)

# Outlier scan (IQR) for numeric
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
out = []
for c in num_cols:
    s = df[c].dropna()
    if len(s) < 20:
        continue
    q1, q3 = np.percentile(s, 25), np.percentile(s, 75)
    iqr = q3 - q1
    if iqr == 0:
        continue
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    cnt = int(((s < lo) | (s > hi)).sum())
    out.append([c, lo, hi, cnt, round(cnt / len(s) * 100, 2)])
outliers = pd.DataFrame(
    out, columns=["numeric_col", "iqr_lower", "iqr_upper", "outlier_count", "outlier_%"]
).sort_values("outlier_%", ascending=False)
display_dataframe_to_user("Potential outliers (IQR rule)", outliers)

# Visual: missingness
miss = df.isna().mean().sort_values(ascending=False)
plt.figure()
miss.plot(kind="bar")
plt.title("Missing values by column (fraction)")
plt.ylabel("Missing fraction")
plt.tight_layout()
plt.show()

# Visual: distributions for key numeric cols
top_num = (
    df[num_cols]
    .var(numeric_only=True)
    .sort_values(ascending=False)
    .head(6)
    .index.tolist()
)
for c in top_num:
    plt.figure()
    df[c].hist(bins=30)
    plt.title(f"Distribution: {c}")
    plt.xlabel(c)
    plt.ylabel("Count")
    plt.tight_layout()
    plt.show()

# ---------- Step 3: Cleaning ----------
df_clean = df.copy()

# Drop duplicate columns (keep first)
to_drop = set([b for a, b in dup_cols])
df_clean = df_clean.drop(columns=list(to_drop), errors="ignore")


def to_int_like(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    if s.dropna().empty:
        return s.astype("Int64")
    frac = (s.dropna() - np.floor(s.dropna())).abs()
    # if all fractional parts ~0, treat as int-like
    if (frac < 1e-9).all():
        return np.floor(s).astype("Int64")
    # else round if it's still mostly int-like
    if (frac < 0.05).mean() > 0.99:
        return np.round(s).astype("Int64")
    return s  # leave numeric float


for c in ["Tenure", "NumOfProducts"]:
    if c in df_clean.columns:
        df_clean[c] = to_int_like(df_clean[c])

# Normalize booleans
bool_cols = ["HasCrCard", "IsActiveMember"]
for c in bool_cols:
    if c in df_clean.columns:
        if str(df_clean[c].dtype) not in ["bool", "boolean"]:
            df_clean[c] = df_clean[c].map(
                {
                    1: True,
                    0: False,
                    "1": True,
                    "0": False,
                    "True": True,
                    "False": False,
                    True: True,
                    False: False,
                }
            )
        df_clean[c] = df_clean[c].astype("boolean")

# Exited as integer 0/1
if "Exited" in df_clean.columns:
    df_clean["Exited"] = to_int_like(df_clean["Exited"])

# Trim whitespace for object cols
for c in df_clean.select_dtypes(include=["object"]).columns:
    df_clean[c] = df_clean[c].astype(str).str.strip()

# Drop duplicates by CustomerId (if any)
before = len(df_clean)
if "CustomerId" in df_clean.columns:
    df_clean = df_clean.drop_duplicates(subset=["CustomerId"], keep="first")
after = len(df_clean)

cleaning_log = pd.DataFrame(
    {
        "action": [
            "Dropped exact duplicate columns",
            "Converted Tenure & NumOfProducts to integer-like",
            "Normalized boolean columns",
            "Converted Exited to integer-like",
            "Trimmed whitespace in text columns",
            "Dropped duplicate CustomerId rows (if any)",
        ],
        "result": [
            f"Dropped {len(to_drop)} columns: {sorted(list(to_drop))}",
            "Done",
            "Done",
            "Done",
            "Done",
            f"Dropped {before - after} rows",
        ],
    }
)
display_dataframe_to_user("Cleaning actions log", cleaning_log)
display_dataframe_to_user("First 5 rows (cleaned)", df_clean.head(5))

# Save cleaned file
cleaned_path = "/mnt/data/bank_data_cleaned_v2.csv"
df_clean.to_csv(cleaned_path, index=False)

# ---------- Step 4: Analysis ----------
# Overall churn
overall_churn = (
    float(df_clean["Exited"].astype(float).mean())
    if "Exited" in df_clean.columns
    else np.nan
)
metrics = pd.DataFrame(
    {
        "metric": ["customers", "overall_churn_rate"],
        "value": [len(df_clean), overall_churn],
    }
)
display_dataframe_to_user("Key metrics", metrics)

# Churn by categorical and boolean
cat_cols = [c for c in df_clean.columns if df_clean[c].dtype == "object"]
for c in ["HasCrCard", "IsActiveMember"]:
    if c in df_clean.columns:
        cat_cols.append(c)
cat_cols = [c for c in cat_cols if c not in ["Surname"]]


def churn_table(col):
    g = df_clean.groupby(col)["Exited"].agg(n="count", churn_rate="mean").reset_index()
    g["churn_rate"] = g["churn_rate"].astype(float)
    return g.sort_values("churn_rate", ascending=False)


churn_tables = {}
for c in cat_cols:
    if df_clean[c].nunique(dropna=True) <= 30:
        churn_tables[c] = churn_table(c)

# Rank by weighted churn variance
info = []
for c, tab in churn_tables.items():
    w = (tab["n"] / tab["n"].sum()).to_numpy()
    p = tab["churn_rate"].to_numpy()
    mu = np.average(p, weights=w)
    wvar = float(np.average((p - mu) ** 2, weights=w))
    info.append([c, wvar, int(tab.shape[0])])
rank = pd.DataFrame(
    info, columns=["column", "weighted_churn_variance", "levels"]
).sort_values("weighted_churn_variance", ascending=False)
display_dataframe_to_user("Category columns ranked by churn spread", rank)

top_cats = rank.head(4)["column"].tolist()
for c in top_cats:
    tab = churn_tables[c]
    display_dataframe_to_user(f"Churn by {c}", tab)
    plt.figure()
    plt.bar(tab[c].astype(str), tab["churn_rate"])
    plt.title(f"Churn rate by {c}")
    plt.ylabel("Churn rate")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()

# Numeric differences by churn
num_cols = [
    c for c in df_clean.select_dtypes(include=[np.number]).columns if c != "Exited"
]
rows = []
for c in num_cols:
    a = df_clean.loc[df_clean["Exited"] == 0, c].dropna().astype(float)
    b = df_clean.loc[df_clean["Exited"] == 1, c].dropna().astype(float)
    if len(a) < 20 or len(b) < 20:
        continue
    rows.append([c, a.mean(), b.mean(), b.mean() - a.mean(), a.median(), b.median()])
num_diff = pd.DataFrame(
    rows,
    columns=[
        "numeric_col",
        "mean_stayed",
        "mean_exited",
        "mean_diff",
        "median_stayed",
        "median_exited",
    ],
)
num_diff["abs_mean_diff"] = num_diff["mean_diff"].abs()
num_diff = num_diff.sort_values("abs_mean_diff", ascending=False).drop(
    columns=["abs_mean_diff"]
)
display_dataframe_to_user("Numeric differences by churn (means & medians)", num_diff)

for c in num_diff.head(4)["numeric_col"].tolist():
    plt.figure()
    data = [
        df_clean.loc[df_clean["Exited"] == 0, c].dropna().astype(float),
        df_clean.loc[df_clean["Exited"] == 1, c].dropna().astype(float),
    ]
    plt.boxplot(data, labels=["Stayed (0)", "Exited (1)"])
    plt.title(f"{c} by churn")
    plt.ylabel(c)
    plt.tight_layout()
    plt.show()

# Correlation matrix
corr = df_clean.select_dtypes(include=[np.number]).astype(float).corr()
if "Exited" in corr.columns:
    corr_exit = (
        corr["Exited"]
        .drop("Exited")
        .sort_values(key=lambda s: s.abs(), ascending=False)
        .to_frame("corr_with_Exited")
    )
    display_dataframe_to_user("Correlation with churn (numeric)", corr_exit)

plt.figure()
plt.imshow(corr.values)
plt.title("Correlation matrix (numeric columns)")
plt.xticks(range(len(corr.columns)), corr.columns, rotation=90)
plt.yticks(range(len(corr.index)), corr.index)
plt.tight_layout()
plt.show()

# Simple model (logistic regression)
try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, accuracy_score

    y = df_clean["Exited"].astype(int)
    X = df_clean.drop(columns=["Exited"])
    X = X.drop(
        columns=[c for c in ["CustomerId", "Surname"] if c in X.columns],
        errors="ignore",
    )

    cat = [
        c for c in X.columns if X[c].dtype == "object" or str(X[c].dtype) == "boolean"
    ]
    num = [c for c in X.columns if c not in cat]

    pre = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
            ("num", "passthrough", num),
        ]
    )

    pipe = Pipeline([("pre", pre), ("lr", LogisticRegression(max_iter=2000))])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    pipe.fit(X_train, y_train)
    proba = pipe.predict_proba(X_test)[:, 1]
    pred = pipe.predict(X_test)
    auc = float(roc_auc_score(y_test, proba))
    acc = float(accuracy_score(y_test, pred))
    perf = pd.DataFrame(
        {"model": ["LogisticRegression (one-hot)"], "ROC_AUC": [auc], "Accuracy": [acc]}
    )
    display_dataframe_to_user("Predictive model performance (baseline)", perf)

    ohe = pipe.named_steps["pre"].named_transformers_["cat"]
    cat_names = ohe.get_feature_names_out(cat)
    feature_names = np.concatenate([cat_names, np.array(num, dtype=object)])
    coefs = pipe.named_steps["lr"].coef_.ravel()
    coef_df = pd.DataFrame({"feature": feature_names, "coef": coefs})
    coef_df["abs_coef"] = coef_df["coef"].abs()
    top_coef = coef_df.sort_values("abs_coef", ascending=False).head(15)[
        ["feature", "coef"]
    ]
    display_dataframe_to_user(
        "Top churn drivers (logistic regression coefficients)", top_coef
    )

    plt.figure()
    plt.barh(top_coef["feature"][::-1], top_coef["coef"][::-1])
    plt.title("Top drivers of churn (logistic regression)")
    plt.xlabel("Coefficient (log-odds)")
    plt.tight_layout()
    plt.show()
except Exception as e:
    display_dataframe_to_user(
        "Modeling note",
        pd.DataFrame(
            {"note": [f"Could not run sklearn model: {type(e).__name__}: {e}"]}
        ),
    )

cleaned_path
