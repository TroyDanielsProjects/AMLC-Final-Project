FROM --platform=linux/amd64 python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["python3", "cleanAndLoadData.py"]
