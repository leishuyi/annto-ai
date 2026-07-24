"""Smart scheduling (mock)"""
from app.schemas.operations import ScheduleRequest, ScheduleResult


def generate_schedule(req: ScheduleRequest) -> ScheduleResult:
    return ScheduleResult(
        assignments=[
            {"driver": "张师傅", "orders": 8, "region": f"{req.region}浦东", "vehicle": "轻卡"},
            {"driver": "李师傅", "orders": 6, "region": f"{req.region}浦西", "vehicle": "面包车"},
            {"driver": "王师傅", "orders": 10, "region": f"{req.region}闵行", "vehicle": "轻卡"},
        ],
        total_drivers=3,
        total_orders=24,
    )
