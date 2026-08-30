# Stage 5 — Dockerfile
#
# Packages the Python app + Streamlit UI only. Ollama is NOT included
# here — it keeps running on the host machine (Windows), and this
# container reaches it via host.docker.internal (see config.py).

FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better layer caching — only re-installs
# when requirements.txt actually changes, not on every code edit)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]