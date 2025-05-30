# Mấy dòng này nếu dùng docker compose
#FROM rasa/rasa:3.6.21

#WORKDIR /app

#COPY models /app/models
#COPY config.yml /app/config.yml
#COPY domain.yml /app/domain.yml
#COPY data /app/data
#COPY endpoints.yml /app/endpoints.yml

#EXPOSE 5005

#CMD ["run", "--enable-api", "--cors", "*", "--model", "models/20250520-151432-greasy-croissant.tar.gz"]

# Mấy dòng này nếu không dùng docker compose
# Bắt đầu từ base image của Rasa
FROM rasa/rasa:3.6.21

# Cài đặt thư viện yêu cầu cho action
USER root

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy các file cấu hình của Rasa
COPY models/20250520-151432-greasy-croissant.tar.gz /app/models/
COPY config.yml /app/config.yml
COPY domain.yml /app/domain.yml
COPY data /app/data
COPY endpoints.yml /app/endpoints.yml

# Expose cổng cho Rasa
EXPOSE 5005

# Khởi động cả Rasa API và Action Server cùng lúc
CMD ["run", "--enable-api", "--cors", "*", "--model", "models/20250520-151432-greasy-croissant.tar.gz"]
