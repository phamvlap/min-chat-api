import dramatiq


@dramatiq.actor(store_results=True)
def check_health_actor_task() -> str:
    return "ok"
