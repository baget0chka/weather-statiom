FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir mysql-connector-python==8.1.0 python-dotenv==1.0.0

COPY data_generator.py .

CMD ["python", "data_generator.py"]