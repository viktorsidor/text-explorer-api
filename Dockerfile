# 1. Použijeme oficiální odlehčený obraz Pythonu postavený na Linuxu
FROM python:3.12-slim

# 2. Nastavení pracovního adresáře uvnitř kontejneru
WORKDIR /code

# 3. Instalace základních Linuxových nástrojů pro kompilaci
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Zkopírování seznamu závislostí
COPY requirements.txt /code/requirements.txt

# 5. Instalace Python balíčků a automatické stažení češtiny z PyPI
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 6. Zkopírování zdrojového kódu aplikace do kontejneru
COPY ./app /code/app

# 7. Informace o portu, na kterém Sanic uvnitř kontejneru poslouchá
EXPOSE 8000

# 8. Spuštění samotného serveru uvnitř Linuxu
CMD ["python", "app/app.py"]