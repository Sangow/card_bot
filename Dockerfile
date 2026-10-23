FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Paketo's lighter builders shipped Python without sqlite3,
# so fail the build early if it is missing
RUN python -c "import sqlite3; print('sqlite', sqlite3.sqlite_version)"

COPY . .

# uid 1000, as with the buildpack, so the files on /data stay accessible
RUN useradd --uid 1000 --no-create-home bot
USER bot

CMD ["python", "app.py"]
