FROM python:3.8-slim-bullseye


COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py app.py

CMD ["python", "app.py"]

