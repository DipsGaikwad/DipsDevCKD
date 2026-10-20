from pathlib import Path
import pandas
import joblib
from sklearn.model_selection import GroupShuffleSplit, GroupKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import precision_recall_curve, auc
from sklearn.metrics import (classification_report, confusion_matrix, 
                             roc_auc_score, accuracy_score, precision_recall_curve, auc)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ML_DATASET = PROJECT_ROOT / "data" / "processed" / "ml_dataset.csv"
MODEL_FILE = PROJECT_ROOT / "models" / "trained" / "ckd_model.joblib"
MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)

df = pandas.read_csv(ML_DATASET)
X = df.drop(columns=['patient_id', 'rapid_progression'])
y = df['rapid_progression']
groups = df['patient_id']

# GroupShuffleSplit ensures no patient overlap
gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
train_idx, test_idx = next(gss.split(X, y, groups))

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
groups_train = groups.iloc[train_idx]

print(f"Training set patients: {len(X_train)}")
print(f"Test set patients: {len(X_test)}")

# Use 'balanced' class weight
pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('classifier', RandomForestClassifier(
        n_estimators=300, max_depth=12, random_state=42, class_weight='balanced'
    ))
])

print("Training longitudinal landmark model...")
pipeline.fit(X_train, y_train)

# Evaluate on test set
y_proba = pipeline.predict_proba(X_test)[:, 1]

# Find optimal threshold on training set to avoid test set leakage
train_proba = pipeline.predict_proba(X_train)[:, 1]
precisions, recalls, thresholds = precision_recall_curve(y_train, train_proba)
f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-8)
best_threshold = thresholds[f1_scores.argmax()]
print(f"\nOptimal Threshold determined from Training Set: {best_threshold:.2f}")

# Apply optimal threshold to test set
y_pred_tuned = (y_proba >= best_threshold).astype(int)

print("\n--- Final Evaluation (Test Set) ---")
test_precisions, test_recalls, _ = precision_recall_curve(y_test, y_proba)
print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")
print(f"PR-AUC: {auc(test_recalls, test_precisions):.4f}")
print(f"Accuracy: {accuracy_score(y_test, y_pred_tuned):.4f}")
print("\nClassification Report (Using Tuned Threshold):")
print(classification_report(y_test, y_pred_tuned, zero_division=0))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred_tuned))

joblib.dump(pipeline, MODEL_FILE)
print(f"Pipeline saved to {MODEL_FILE}")