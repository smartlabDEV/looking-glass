"""
AI-anbefalingsrouter.

Bruker regelbasert route_optimizer som prototype.
TODO: Koble til ekte XGBoost-modell fra ml/models/route_optimizer.pkl
"""

from fastapi import APIRouter, Query
from models.route_optimizer import recommend

router = APIRouter(tags=["ai"])


@router.get("/recommend")
async def get_recommendation(
    use_case: str = Query(..., description="gaming | streaming | work"),
    source_a: str = Query(..., description="ID til første kilde"),
    source_b: str = Query(..., description="ID til andre kilde"),
):
    """
    Returnerer AI-anbefaling om hvilken kilde som er best for gitt brukstilfelle.
    Modellen tar hensyn til tidspunkt på dagen og historiske målinger.
    """
    # TODO: implement real ML prediction – se ml/predict.py
    return recommend(use_case=use_case, source_a=source_a, source_b=source_b)
