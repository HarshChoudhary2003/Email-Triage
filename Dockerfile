FROM python:3.11-slim

# Create user with UID 1000
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Install dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=user . .

# HuggingFace Spaces runs on port 7860
EXPOSE 7860

# Environment variables (override at runtime)
ENV API_BASE_URL="https://api.openai.com/v1"
ENV MODEL_NAME="gpt-4o-mini"
ENV HF_TOKEN=""

# Run application
CMD ["python", "app.py"]
