FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && useradd -r -u 10001 appuser
COPY app.py wsgi.py ./
USER 10001
EXPOSE 5002
CMD ["gunicorn", "--preload", "-b", "0.0.0.0:5002", "-w", "2", "--timeout", "60", "wsgi:app"]
