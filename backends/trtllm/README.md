# TRT-LLM Qwen3-30B-A3B-FP4 Server

TensorRT-LLM を使用した Qwen3-30B-A3B-FP4 モデルのサービング環境。

## 前提条件

- Docker with NVIDIA Container Toolkit
- NVIDIA GPU（VRAM 24GB以上推奨）
- モデルウェイト（`~/model_weights` に配置済み）

## 起動

```bash
docker compose up
```

## API

OpenAI互換APIがポート8000で公開されます。

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia/Qwen3-30B-A3B-FP4",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 128
  }'
```

## Thinking モード

Qwen3はデフォルトで **thinking モード（有効）** で動作します。レスポンスに `<think>` タグで思考プロセスが含まれます。

### Non-thinking モードへの切り替え

システムプロンプトに `/no_think` を追加すると、思考プロセスを出力せずに回答のみを返します。

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia/Qwen3-30B-A3B-FP4",
    "messages": [
      {"role": "system", "content": "/no_think"},
      {"role": "user", "content": "Hello"}
    ],
    "max_tokens": 128
  }'
```

### 備考

thinking モード使用時は、クライアント側でレスポンスから `<think>...</think>` タグを除去する必要があります。
