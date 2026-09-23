FROM python:3.11-slim

# Outils de compilation C
RUN apt-get update && apt-get install -y \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier tout le projet
COPY . .

# Compiler les binaires C (adaptez les noms de fichiers sources)
# Exemple :
# RUN gcc -O2 -o Work/HRS Src/HRS.c -lm
# RUN gcc -O2 -o Work/SHS Src/SHS.c -lm
# RUN gcc -O2 -o Work/sphere_SHS Src/sphere_SHS.c -lm

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]