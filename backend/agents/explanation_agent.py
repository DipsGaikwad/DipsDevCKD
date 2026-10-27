import shap
import numpy as np
from backend.agents.prediction_agent import pipeline

classifier = pipeline.named_steps['classifier']
explainer = shap.TreeExplainer(classifier)

def explain_prediction(features_df):
    try:
        shap_values = explainer.shap_values(features_df)
        
        # Handle different SHAP output shapes safely
        if isinstance(shap_values, list):
            vals = shap_values[1][0] # Older SHAP: list of arrays
        elif len(shap_values.shape) == 3:
            vals = shap_values[0, :, 1] # Newer SHAP: (1, num_features, 2)
        else:
            vals = shap_values[0] 
            
        # Flatten to ensure it's a 1D array of scalars
        vals = np.array(vals).flatten()
            
        top_indices = np.argsort(-np.abs(vals))[:3]
        explanations = []
        feature_names = features_df.columns.tolist()
        
        for idx in top_indices:
            impact = float(vals[idx])
            explanations.append({
                "feature": feature_names[idx],
                "impact": round(impact, 4),
                "direction": "increases" if impact > 0 else "decreases"
            })
        return explanations
    except Exception as e:
        return [{"error": f"SHAP explanation failed: {str(e)}"}]