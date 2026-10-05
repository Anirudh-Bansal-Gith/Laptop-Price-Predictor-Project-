"""FastAPI dependency injection and application state caching.

Handles lazy-loading and thread-safe persistence of serialized scikit-learn
model pipelines across the application lifecycle.
"""

from typing import Any, Optional
import os
import joblib


_model_instance: Optional[Any] = None


def load_model_on_startup() -> Optional[Any]:
    """Load model artifact into shared memory on server initialization.

    Returns:
        Optional[Any]: Loaded model pipeline, or None if artifact file is absent.
    """
    global _model_instance
    model_path = os.environ.get("MODEL_PATH", "models/best_model.pkl")

    if os.path.exists(model_path):
        _model_instance = joblib.load(model_path)
        print(f"Model loaded successfully from {model_path}")
    else:
        print(f"Warning: Model artifact not found at {model_path}.")
        print("Execute 'python -m src.models.train' to compile and export the model.")
        _model_instance = None

    return _model_instance


def get_model() -> Optional[Any]:
    """Dependency provider returning active model pipeline instance.

    Performs lazy loading if the model has not been initialized.

    Returns:
        Optional[Any]: Active model instance or None.
    """
    global _model_instance
    if _model_instance is None:
        load_model_on_startup()
    return _model_instance
