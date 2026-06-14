FROM python:3.13-slim

WORKDIR /app

COPY Lr3/parser/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Lr2/task2/ ./
COPY Lr3/parser/ ./
