from app import app

print("Lista de todas las rutas registradas:")
print("-" * 50)
for rule in app.url_map.iter_rules():
    print(f"Endpoint: {rule.endpoint}")
    print(f"URL: {rule}")
    print(f"Métodos: {', '.join(rule.methods)}")
    print("-" * 50)
