FROM mcr.microsoft.com/playwright/python:v1.56.0-jammy

WORKDIR /project

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["python", "-m", "app.app"]
