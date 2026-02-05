# dgx-llm-serve

DGX Spark OEM機向け LLM 推論バックエンドの Docker Compose 設定を統合管理するリポジトリ。

## バックエンド一覧

| バックエンド | 技術 | 対応モデル | 特徴 |
|-------------|------|-----------|------|
| [trtllm](backends/trtllm/) | TensorRT-LLM | Qwen3-30B-A3B-FP4 | Thinking モード対応 |
| [vllm](backends/vllm/) | vLLM | Qwen3-Coder, Nemotron, Nemotron-VL | ツール呼び出し対応 |
| [nim](backends/nim/) | NVIDIA NIM | Qwen3-32B, Llama-3.1-8B, Nemotron-Nano | NGC マネージドイメージ |

## 前提条件

- NVIDIA GPU（VRAM 24GB 以上推奨）
- Docker + Docker Compose
- NVIDIA Container Toolkit
- モデルウェイト: `~/model_weights/` に配置（NIM を除く）

## クイックスタート

```bash
# TensorRT-LLM (Qwen3-30B)
cd backends/trtllm && docker compose up

# vLLM (Qwen3-Coder)
cd backends/vllm && docker compose --profile qwen up

# NVIDIA NIM (Qwen3-32B)
cd backends/nim && docker compose up
```

## API テスト

全バックエンドで OpenAI 互換 API がポート 8000 で公開されます。

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<MODEL_NAME>",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 128
  }'
```

## ドキュメント

- [Thinking モード](docs/thinking-mode.md) - Qwen3 の思考プロセス出力
- [ツール呼び出し](docs/tool-calling.md) - vLLM でのツール呼び出し設定とデバッグ
