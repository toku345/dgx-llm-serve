# dgx-llm-serve

[NVIDIA DGX Spark](https://marketplace.nvidia.com/en-us/enterprise/personal-ai-supercomputers/dgx-spark/) および OEM 機向けの LLM 推論バックエンド設定集。

> **注意**: 本リポジトリは DGX Spark / OEM 機専用です。他の環境での動作は想定していません。

## 対象ハードウェア

- [NVIDIA DGX Spark](https://marketplace.nvidia.com/en-us/enterprise/personal-ai-supercomputers/dgx-spark/)
- OEM 機（[Lenovo ThinkStation PGX](https://www.lenovo.com/us/en/p/workstations/thinkstation-p-series/lenovo-thinkstation-pgx-sff/30kl0002us) 等）

### 動作確認環境

- Lenovo ThinkStation PGX

## バックエンド

| バックエンド | 技術 | 対応モデル | 特徴 |
|-------------|------|-----------|------|
| [vllm](backends/vllm/) | vLLM | Qwen3.6-35B-A3B-FP8 | MoE 3B Active、ツール呼び出し、thinking 分離、128K context |

AI コーディングエージェント / Web サイト解析など多用途を単一モデルでカバーする精選構成。

## 前提条件

- DGX Spark または OEM 機（GB10 Grace Blackwell）
- Docker + Docker Compose
- NVIDIA Container Toolkit
- モデルウェイト: `~/model_weights/Qwen/Qwen3.6-35B-A3B-FP8/` に配置

## クイックスタート

```bash
# モデル重みのダウンロード（初回のみ、約 36 GiB）
uv tool install "huggingface_hub[cli]"
hf download Qwen/Qwen3.6-35B-A3B-FP8 \
  --local-dir ~/model_weights/Qwen/Qwen3.6-35B-A3B-FP8

# 起動
cd backends/vllm && docker compose --profile qwen36 up
```

## API テスト

OpenAI 互換 API がポート 8000 で公開されます。

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.6-35B-A3B-FP8",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 128
  }'
```

## ドキュメント

- [Thinking モード](docs/thinking-mode.md) - Qwen3 の思考プロセス出力
- [ツール呼び出し](docs/tool-calling.md) - vLLM でのツール呼び出し設定とデバッグ
- [モデル精選設計書](docs/plans/2026-04-24-model-curation-design.md) - 精選の経緯と判断

## セキュリティに関する注意事項

本リポジトリは個人利用・ローカル実行を想定しています。

### デフォルト設定

- **ポートバインド**: `127.0.0.1:8000` （ローカルホストのみ）
- **API 認証**: なし（ローカル実行前提）

### LAN 内の他デバイスからアクセスする場合

`backends/vllm/compose.yml` のポート設定を変更してください:

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
