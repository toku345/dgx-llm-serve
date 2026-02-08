# dgx-llm-serve

[NVIDIA DGX Spark](https://marketplace.nvidia.com/en-us/enterprise/personal-ai-supercomputers/dgx-spark/) および OEM 機向けの LLM 推論バックエンド設定集。

> **注意**: 本リポジトリは DGX Spark / OEM 機専用です。他の環境での動作は想定していません。

## 対象ハードウェア

- [NVIDIA DGX Spark](https://marketplace.nvidia.com/en-us/enterprise/personal-ai-supercomputers/dgx-spark/)
- OEM 機（[Lenovo ThinkStation PGX](https://www.lenovo.com/us/en/p/workstations/thinkstation-p-series/lenovo-thinkstation-pgx-sff/30kl0002us) 等）

### 動作確認環境

- Lenovo ThinkStation PGX

## バックエンド一覧

| バックエンド | 技術 | 対応モデル | 特徴 |
|-------------|------|-----------|------|
| [trtllm](backends/trtllm/) | TensorRT-LLM | Qwen3-30B-A3B-FP4 | Thinking モード対応 |
| [vllm](backends/vllm/) | vLLM | Qwen3-Coder, Nemotron, Nemotron-VL | ツール呼び出し対応 |
| [nim](backends/nim/) | NVIDIA NIM | Qwen3-32B, Llama-3.1-8B, Nemotron-Nano | NGC マネージドイメージ |

## 前提条件

- DGX Spark または OEM 機（GB10 Grace Blackwell）
- Docker + Docker Compose
- NVIDIA Container Toolkit
- モデルウェイト: `~/model_weights/` に配置（NIM を除く）

## クイックスタート

```bash
# TensorRT-LLM (Qwen3-30B)
cd backends/trtllm && docker compose up

# vLLM (Qwen3-Coder)
cd backends/vllm && docker compose --profile qwen up

# vLLM マルチモデル (Qwen3-Coder + Nemotron を単一ポートで同時起動)
cd backends/vllm && docker compose --profile multi up

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

## セキュリティに関する注意事項

本リポジトリは個人利用・ローカル実行を想定しています。

### デフォルト設定

- **ポートバインド**: `127.0.0.1:8000` （ローカルホストのみ）
- **API 認証**: なし（ローカル実行前提）

### LAN 内の他デバイスからアクセスする場合

各 `compose.yml` のポート設定を変更してください:

```yaml
# 変更前（ローカルのみ）
ports:
  - "127.0.0.1:8000:8000"

# 変更後（LAN 公開）
ports:
  - "8000:8000"
```

**注意**: LAN 公開時は以下を確認してください:
- ルーターでポート 8000 への外部（インターネット）アクセスがブロックされていること
- LAN 内の信頼できるデバイスのみがアクセスすること

### リモートコード実行に関する注意

vLLM の Nemotron モデル（`--trust-remote-code` フラグ）は HuggingFace からのコード実行を許可しています:
- サプライチェーン攻撃のリスクが存在します
- モデル初回ダウンロード時に `~/.cache/huggingface` 内のコードを確認することを推奨します
