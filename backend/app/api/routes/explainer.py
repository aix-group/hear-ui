# app/api/routes/explainer.py

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Import PatientData from predict to ensure consistent input processing
from app.api.routes.predict import PatientData

router = APIRouter(prefix="/explainer", tags=["explainer"])


class ShapVisualizationResponse(BaseModel):
    """Response with SHAP values and optional plot."""

    prediction: float
    feature_importance: dict[str, float]
    feature_values: dict[str, float] | None = None
    shap_values: list[float]
    base_value: float
    plot_base64: str | None = None
    top_features: list[dict] | None = None
    warnings: list[str] = []


@router.get("/methods", summary="List Available XAI Methods")
async def list_explainer_methods():
    """List all available explainer methods.

    Returns:
        List of available XAI method names and their descriptions
    """
    from app.core.explainer_registry import get_available_explainers

    methods = get_available_explainers()

    # Add descriptions
    descriptions = {
        "shap": "SHAP (SHapley Additive exPlanations) - Model-agnostic explanations",
        "coefficient": "Coefficient-based - Fast explanations for linear models",
        "coef": "Alias for 'coefficient'",
        "linear": "Alias for 'coefficient'",
        "lime": "LIME (Local Interpretable Model-agnostic Explanations) - Requires lime package",
    }

    return {
        "methods": [
            {
                "name": method,
                "description": descriptions.get(method, "No description available"),
            }
            for method in methods
        ]
    }


@router.post(
    "/explain", response_model=ShapVisualizationResponse, summary="Get SHAP Explanation"
)
@router.post(
    "/shap",
    response_model=ShapVisualizationResponse,
    summary="Get SHAP Explanation (Alias)",
    include_in_schema=False,  # Hidden alias for backward compatibility
)
async def get_shap_explanation(
    request: PatientData,
    include_plot: bool = Query(default=False, description="Include visualization plot"),
    method: str = Query(
        default="shap",
        description="XAI method to use (shap, coefficient, lime)",
    ),
):
    """Generate explanation with configurable XAI method.

    Supports multiple explanation methods:
    - shap: SHAP-based explanations (default)
    - coefficient: Fast coefficient-based explanations for linear models
    - lime: LIME explanations (requires lime package)
    """
    try:
        from app.main import app as fastapi_app

        wrapper = getattr(fastapi_app.state, "model_wrapper", None)
    except Exception:
        wrapper = None

    if not wrapper or not wrapper.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Explanations require a loaded model.",
        )

    logger = logging.getLogger(__name__)

    try:
        from app.core.explainer_registry import create_explainer

        # Convert request to dict with original column names (aliases)
        # Use same processing as /predict endpoint
        # exclude_none=True: don't send None values (let preprocessor use its defaults)
        feature_dict = request.model_dump(by_alias=True, exclude_none=True)

        logger = logging.getLogger(__name__)
        logger.debug("feature_dict: %s", feature_dict)

        # Get prediction using the raw dict (wrapper.predict handles preprocessing)
        # clip=True enforces probability bounds [1%, 99%]
        model_res = wrapper.predict(feature_dict, clip=True)
        try:
            prediction = float(model_res[0])
        except (TypeError, IndexError):
            prediction = float(model_res)

        logger.debug("model_res: %s, prediction: %s", model_res, prediction)

        # Now prepare the preprocessed data separately for the explainer
        # (explainer needs the transformed features)
        preprocessed = wrapper.prepare_input(feature_dict)

        logger.debug(
            "preprocessed shape: %s",
            preprocessed.shape if hasattr(preprocessed, "shape") else len(preprocessed),
        )

        # Create explainer using factory
        try:
            explainer = create_explainer(
                method=method,
                model=wrapper.model,
                feature_names=wrapper.get_feature_names(),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Generate explanation
        explanation = explainer.explain(
            model=wrapper.model,
            input_data=preprocessed,
            feature_names=wrapper.get_feature_names(),
            include_plot=include_plot,
        )

        # Convert to response format
        # Sort features by absolute importance
        sorted_features = sorted(
            explanation.feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        top_features = [
            {"name": name, "importance": float(importance)}
            for name, importance in sorted_features[:10]
        ]

        # Get SHAP values as list (for backward compatibility)
        shap_values = [
            explanation.feature_importance.get(name, 0.0)
            for name in wrapper.get_feature_names()
        ]

        # Get plot if available
        plot_base64 = None
        if include_plot and explainer.supports_visualization():
            plot_base64 = explainer.generate_visualization(explanation)
        elif explanation.metadata and "plot_base64" in explanation.metadata:
            plot_base64 = explanation.metadata.get("plot_base64")

        return ShapVisualizationResponse(
            prediction=prediction,  # Use wrapper prediction, not explainer
            feature_importance=explanation.feature_importance,
            feature_values=explanation.feature_values,
            shap_values=shap_values,
            base_value=explanation.base_value,
            plot_base64=plot_base64,
            top_features=top_features,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Explanation generation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Explanation failed: {str(exc)}",
        )
