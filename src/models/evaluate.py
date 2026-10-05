"""Model evaluation and metrics calculation module.

Provides standardized regression evaluation across:
- Coefficient of Determination (R2 Score).
- Mean Absolute Error (MAE).
- Root Mean Squared Error (RMSE).
- Mean Absolute Percentage Error (MAPE).
"""

from typing import Dict, Any
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def evaluate_model(model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Compute standard regression metrics on test partitions.

    Args:
        model: Trained scikit-learn estimator or pipeline implementing `.predict()`.
        X_test: Test predictor features.
        y_test: Ground-truth continuous target vector.

    Returns:
        Dict[str, float]: Evaluated metrics:
            - 'r2': Coefficient of determination.
            - 'mae': Mean absolute error.
            - 'rmse': Root mean squared error.
            - 'mape': Mean absolute percentage error.
    """
    predictions = model.predict(X_test)

    r2 = float(r2_score(y_test, predictions))
    mae = float(mean_absolute_error(y_test, predictions))
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))

    # Calculate MAPE safely preventing division by zero
    non_zero_mask = y_test != 0
    mape = float(
        np.mean(np.abs((y_test[non_zero_mask] - predictions[non_zero_mask]) / y_test[non_zero_mask]))
        * 100
    )

    return {
        "r2": round(r2, 4),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
    }
