def test_api_module_imports():
    from app.main import app
    assert app.title == "CloudGuard CSPM API"
    assert any(route.path == "/api/dashboard" for route in app.routes)
