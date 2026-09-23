FROM python:3.11-slim

# Installer gcc et les outils nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier le code source + le reste
COPY . .

# Compiler les programmes C (versions Linux)
RUN gcc -O2 -o Work/HRS Src/HRS.c -lm
RUN gcc -O2 -o Work/SHS Src/SHS.c -lm
RUN gcc -O2 -o Work/sphere_SHS Src/sphere_SHS.c -lm

# Rendre les binaires exécutables
RUN chmod +x Work/HRS Work/SHS Work/sphere_SHS

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]