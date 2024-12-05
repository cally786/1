#!/bin/bash

# URL base
BASE_URL="http://localhost:5000"

echo "1. Iniciando sesión como admin..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "admin123"}')

# Extraer el token de la respuesta (ajusta esto según el formato de tu respuesta)
# TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

echo "\n2. Creando nuevo equipo..."
curl -X POST "$BASE_URL/api/equipment" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Equipo Test Curl",
    "description": "Equipo para pruebas con curl",
    "quantity": 5,
    "category": "Test",
    "location": "Almacén A"
  }'

echo "\n3. Verificando estado del equipo..."
curl -X GET "$BASE_URL/api/equipment/1"

echo "\n4. Actualizando cantidad del equipo..."
curl -X PUT "$BASE_URL/api/equipment/1" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 0
  }'

echo "\n5. Verificando nuevo estado del equipo..."
curl -X GET "$BASE_URL/api/equipment/1"

echo "\n6. Creando transacción..."
curl -X POST "$BASE_URL/api/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": 1,
    "quantity": 5,
    "type": "Salida",
    "description": "Prueba con curl"
  }'

echo "\n7. Verificando estado final del equipo..."
curl -X GET "$BASE_URL/api/equipment/1"
