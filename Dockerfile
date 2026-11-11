FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir pynacl cryptography "webauthn==3.0.1"

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["python3", "server.py"]
