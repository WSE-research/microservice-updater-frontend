FROM python:3.10-slim 
# pyarrow doesn't support 3.11 yet
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y build-essential curl software-properties-common && rm -rf /var/lib/apt/lists/*
RUN pip3 install -r requirements.txt
HEALTHCHECK CMD curl --fail http://localhost:4000/_stcore/health
ENTRYPOINT streamlit run app.py --server.enableStaticServing true --server.port=4000 --server.address=0.0.0.0