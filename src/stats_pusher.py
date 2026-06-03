from prometheus_client import CollectorRegistry, Counter, make_asgi_app

registry = CollectorRegistry()

service_requests_counter = Counter(
    "requests_to_service",
    "Total number of requests to the service",
    ["service"],
    registry=registry,
)

user_requests_counter = Counter(
    "requests_by_user",
    "Number of requests by user",
    ["user_id"],
    registry=registry,
)

metrics_app = make_asgi_app(registry)


async def stats_pusher(service_name: str, user_id: str):
    service_requests_counter.labels(service=service_name).inc()
    user_requests_counter.labels(user_id=user_id).inc()
