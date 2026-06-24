from app.dependencies.auth import get_current_user
from app.routers.content import router


def test_content_router_has_no_router_level_auth_dependency() -> None:
    assert router.dependencies == []


def test_no_content_route_depends_on_get_current_user() -> None:
    for route in router.routes:
        dependant_calls = [dep.call for dep in route.dependant.dependencies]
        assert get_current_user not in dependant_calls
