FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-dev \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3.10 /usr/bin/python

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN python -c "from transformers import AutoTokenizer, EsmForProteinFolding; \
    print('📥 Téléchargement du modèle ESMFold v1 (15GB)...'); \
    AutoTokenizer.from_pretrained('facebook/esmfold_v1'); \
    EsmForProteinFolding.from_pretrained('facebook/esmfold_v1', low_cpu_mem_usage=True); \
    print('✅ Modèle téléchargé avec succès!')"

RUN mkdir -p /app/data/outputs

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]