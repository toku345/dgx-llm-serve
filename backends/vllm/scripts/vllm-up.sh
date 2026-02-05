#!/bin/bash

docker run -it \
    --gpus all \
    --ipc=host \
    -p 8000:8000 \
    -v "$HOME/model_weights:/app/model" \
    nvcr.io/nvidia/vllm:25.11-py3 \
    vllm serve /app/model \
    --host 0.0.0.0 \
    --port 8000 \
    --served-model-name Qwen/Qwen3-Coder-30B-A3B-Instruct \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 32768 \
    --trust-remote-code \
    --enable-auto-tool-choice \
    --tool-call-parser hermes
