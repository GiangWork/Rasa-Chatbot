FROM rasa/rasa:3.6.21

WORKDIR /app

COPY models /app/models
COPY config.yml /app/config.yml
COPY domain.yml /app/domain.yml
COPY data /app/data
COPY endpoints.yml /app/endpoints.yml

CMD ["run", "--enable-api", "--cors", "*", "--model", "models/20250520-151432-greasy-croissant.tar.gz"]
