"""Driver navigation (mock)"""
from app.schemas.driver import RouteRequest, RouteResult


def get_route(req: RouteRequest) -> RouteResult:
    return RouteResult(
        waypoints=[
            {"name": req.origin, "type": "start"},
            {"name": "沪蓉高速入口", "type": "highway"},
            {"name": "上海绕城", "type": "highway"},
            {"name": req.destination, "type": "end"},
        ],
        total_km=1850.0,
        estimated_min=1200,
        traffic_delay_min=15,
    )
