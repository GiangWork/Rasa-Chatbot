FROM rasa/rasa:3.6.21

USER root

WORKDIR /app

# Copy các file cấu hình của Rasa
COPY models/20250520-151432-greasy-croissant.tar.gz /app/models/
COPY config.yml /app/config.yml
COPY domain.yml /app/domain.yml
COPY data /app/data
COPY endpoints.yml /app/endpoints.yml

# EXPOSE phải dùng biến PORT
EXPOSE 5005

ENTRYPOINT []

CMD ["sh", "-c", "rasa run --enable-api --cors '*' --port ${PORT:-5005} --model models/20250520-151432-greasy-croissant.tar.gz"]
