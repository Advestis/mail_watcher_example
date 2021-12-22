FROM python:3.9-slim
COPY ./ /watcher
WORKDIR /watcher
RUN pip install -U pip && pip install -r requirements.txt