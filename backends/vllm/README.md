# vLLM Backend

vLLM を使用した LLM サービング環境。

## 対応モデル

| プロファイル | モデル | 特徴 |
|-------------|--------|------|
| qwen | Qwen3-Coder-30B-A3B-Instruct | ツール呼び出し対応 |
| nemotron | NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 | 高速推論 |
| nemotron-vl | NVIDIA-Nemotron-Nano-12B-v2-VL | マルチモーダル（画像対応）|

## 起動

```bash
# Qwen3-Coder (ツール呼び出し対応)
docker compose --profile qwen up

# Nemotron
docker compose --profile nemotron up

# Nemotron-VL (マルチモーダル)
docker compose --profile nemotron-vl up
```

## 設定パラメータ

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| `--gpu-memory-utilization` | 0.9 | GPU メモリ使用率 |
| `--max-model-len` | 32768 | 最大コンテキスト長 |
| `--max-num-seqs` | 4 | 最大並行シーケンス数 |
| `--tensor-parallel-size` | 1 | テンソル並列数 |

## ツール呼び出し

Qwen3-Coder でツール呼び出しを使用する場合:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    "messages": [{"role": "user", "content": "What is the weather in Tokyo?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get weather information",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string"}
          },
          "required": ["location"]
        }
      }
    }],
    "tool_choice": "auto"
  }'
```

詳細は [ツール呼び出しガイド](../../docs/tool-calling.md) を参照。

## 環境要件

- NVIDIA GPU + nvidia-container-toolkit
- モデルウェイト: `~/model_weights/` に配置
