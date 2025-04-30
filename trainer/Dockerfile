FROM nvidia/cuda:12.3.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y python3.11 python3-pip && \
    ln -s /usr/bin/python3.11 /usr/bin/python3 && \
    pip3 install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["python3", "finetune.py"]