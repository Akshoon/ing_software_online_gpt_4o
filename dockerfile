FROM python:3.9-slim
RUN apt-get update && apt-get install -y tk8.6-dev tcl8.6-dev && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 80
CMD ["python", "gui.py"]
