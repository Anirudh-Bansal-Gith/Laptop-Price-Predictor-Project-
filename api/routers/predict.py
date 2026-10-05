"""Prediction router endpoint handling POST /predict requests.

Accepts validated hardware specifications, checks model availability,
executes inference through `src.models.predict`, and returns valuation results.
"""

from fastapi import APIRouter, HTTPException, status

from api.dependencies import get_model
from api.schemas import LaptopFeatures, PricePrediction
from src.models.predict import predict_price
from src.utils.helpers import format_price

router = APIRouter(tags=["Predictions"])


@router.post(
    "/predict",
    response_model=PricePrediction,
    status_code=status.HTTP_200_OK,
    summary="Estimate laptop market price",
    description="Accepts hardware specifications and computes an estimated market valuation using trained ML pipelines.",
)
async def predict_laptop_price(features: LaptopFeatures) -> PricePrediction:
    """Handle POST prediction requests.

    Args:
        features: Validated LaptopFeatures instance.

    Returns:
        PricePrediction: Estimated price valuation and formatting details.

    Raises:
        HTTPException: 503 if model is not loaded, 500 if inference fails.
    """
    model = get_model()
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Machine learning model is not loaded. Train and serialize model to models/best_model.pkl first.",
        )

    try:
        spec_dict = features.model_dump()
        predicted_val = predict_price(model, spec_dict)
        return PricePrediction(
            predicted_price=predicted_val,
            currency="EUR",
            formatted_price=format_price(predicted_val, "EUR"),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {str(exc)}",
        ) from exc
