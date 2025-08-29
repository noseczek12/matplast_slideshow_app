# Dockerfile

# Krok 1: Użyj oficjalnego, lekkiego obrazu Python jako bazy
FROM python:3.9-slim

# Krok 2: Ustaw katalog roboczy wewnątrz kontenera
WORKDIR /app

# Krok 3: Skopiuj plik z zależnościami i zainstaluj je
# Używamy --no-cache-dir, aby zmniejszyć rozmiar finalnego obrazu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Krok 4: Skopiuj resztę plików aplikacji do kontenera
COPY . .

# Krok 5: Wystaw port, na którym będzie działać aplikacja wewnątrz kontenera
EXPOSE 5000

# Krok 6: Komenda, która uruchomi aplikację przy starcie kontenera
# Używamy gunicorn z workerem eventlet, co jest wymagane przez Flask-SocketIO
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "app:app"]