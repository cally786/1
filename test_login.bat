@echo off
echo === Probando login con form-data ===

echo.
echo 1. Intentando login como admin...
curl -v -X POST "http://localhost:5000/login" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=admin&password=admin123" ^
  -c cookies.txt

echo.
echo === Contenido del archivo cookies.txt ===
type cookies.txt

pause
