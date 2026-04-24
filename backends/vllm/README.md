# vLLM Backend

vLLM を使用した LLM サービング環境。

## 対応モデル

| プロファイル | モデル | 特徴 |
|-------------|--------|------|
| qwen36 | Qwen3.6-35B-A3B-FP8 | MoE 35B total / 3B active, FP8 量子化, thinking モード（`reasoning_content` 分離）, tool calling（`qwen3_coder` parser）, 128K context |

## 起動

```bash
docker compose --profile qwen36 up
```

初回起動はモデルロードに数分かかります。`curl http://localhost:8000/health` が 200 を返せば起動完了です。

## モデル重みのダウンロード

```bash
# 初回のみ（約 36 GiB）
uv tool install "huggingface_hub[cli]"
hf download Qwen/Qwen3.6-35B-A3B-FP8 \
  --local-dir ~/model_weights/Qwen/Qwen3.6-35B-A3B-FP8
```

## API テスト

```bash
# 通常 chat
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen3.6-35B-A3B-FP8", "messages": [{"role": "user", "content": "Hello"}]}'

# Thinking モード（`reasoning_content` に思考プロセス分離）
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.6-35B-A3B-FP8",
    "messages": [{"role": "user", "content": "Explain why the sky is blue."}],
    "max_tokens": 1000
  }' | jq '.choices[0].message | {content, reasoning_content}'
```

## 設定パラメータ

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| `image` | `vllm/vllm-openai:v0.19.0-aarch64-cu130-ubuntu2404` | ARM64 / CUDA 13.0 / Ubuntu 24.04 明示 pin |
| `--gpu-memory-utilization` | `0.8` | 重み ~36 GiB + KV cache + 余裕 |
| `--max-model-len` | `131072` | 128K context（公式 262K は TP=8 前提） |
| `--max-num-seqs` | `4` | 最大並行シーケンス数 |
| `--tensor-parallel-size` | `1` | テンソル並列数 |
| `--reasoning-parser` | `qwen3` | thinking を `reasoning_content` に分離 |
| `--tool-call-parser` | `qwen3_coder` | Qwen3 系 tool calling parser |

## トラブルシューティング

- **起動が遅い**: 初回は数分かかります。`docker logs vllm-vllm-qwen36-1 -f` で進捗確認
- **GPU OOM**: `--gpu-memory-utilization` を 0.7 まで下げる、または `--max-model-len` を 65536 に縮小
- **404 unknown model**: `model` フィールドに `Qwen/Qwen3.6-35B-A3B-FP8` を指定
- **cuda capability 12.1 警告**: PyTorch 公式最大 12.0 を超過する警告が出るが、互換動作します

## ツール呼び出し

詳細は [ツール呼び出しガイド](../../docs/tool-calling.md) を参照。

## 環境要件

- NVIDIA GPU + nvidia-container-toolkit
- モデルウェイト: `~/model_weights/Qwen/Qwen3.6-35B-A3B-FP8/` に配置
