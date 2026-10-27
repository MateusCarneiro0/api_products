FROM python:3.13.18-slim AS builder

WORKDIR /app

RUN python -m venv /app/venv

ENV PATH="/app/venv/bin:$PATH"

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

FROM python:3.13.18-slim

WORKDIR /app

COPY --from=builder /app/venv/ /app/venv/

COPY . /app/

ENV PATH="/app/venv/bin:$PATH"

EXPOSE 3000

CMD ["gunicorn","--bind","0.0.0.0:3000","app:app"]

