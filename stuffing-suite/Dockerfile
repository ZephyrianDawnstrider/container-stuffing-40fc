FROM python:3.12-slim
WORKDIR /app
COPY requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY app.py planner.py ./
COPY config ./config
RUN useradd --create-home appuser
USER appuser
ENV PYTHONUNBUFFERED=1
CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true --server.maxUploadSize=5 --browser.gatherUsageStats=false"]
