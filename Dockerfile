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
COPY models /app/models
COPY config.yml /app/config.yml
COPY domain.yml /app/domain.yml
COPY data /app/data
COPY endpoints.yml /app/endpoints.yml

# Copy action và các yêu cầu cho custom action
COPY ./actions /app/actions
COPY ./actions/actions_requirements.txt /app/actions/actions_requirements.txt

# Cài đặt pip và các dependencies cho custom action
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/actions/actions_requirements.txt

# Trở lại user mặc định của Rasa SDK
USER 1001

# Expose cổng cho Rasa và Action Server
EXPOSE 5005 5055

ENTRYPOINT []

# Khởi động cả Rasa API và Action Server cùng lúc
CMD rasa run --enable-api --cors '*' --model models/20250520-151432-greasy-croissant.tar.gz & python -m rasa_sdk --actions actions
