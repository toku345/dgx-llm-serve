# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

DGX Spark OEM機向け LLM 推論バックエンド（TensorRT-LLM, vLLM, NVIDIA NIM）を Docker Compose で管理するモノレポジトリ。

## ディレクトリ構造

```
dgx-llm-serve/
├── backends/
│   ├── trtllm/    # TensorRT-LLM (Qwen3-30B-A3B-FP4)
│   ├── vllm/      # vLLM (Qwen3-Coder, Nemotron, Nemotron-VL)
│   └── nim/       # NVIDIA NIM (DGX Spark 向け)
├── docs/          # 共通ドキュメント
└── scripts/       # ユーティリティスクリプト
```

## コマンド

### サーバー起動

```bash
# TensorRT-LLM
cd backends/trtllm && docker compose up

# vLLM (プロファイル選択)
cd backends/vllm && docker compose --profile qwen up
cd backends/vllm && docker compose --profile nemotron up
cd backends/vllm && docker compose --profile nemotron-vl up

# NVIDIA NIM
cd backends/nim && docker compose up
```

### ヘルスチェック

```bash
curl http://localhost:8000/health
```

### API テスト

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "<MODEL_NAME>", "messages": [{"role": "user", "content": "Hello"}]}'
```

## バックエンド固有の注意事項

### TensorRT-LLM
- Thinking モード: デフォルトで有効。`/no_think` をシステムプロンプトに追加で無効化
- クライアント側で `<think>...</think>` タグの除去が必要

### vLLM
- ツール呼び出し対応（Qwen3-Coder）
- 内部プロンプト確認: `echo: true` パラメータを使用
- 設定パラメータ: `--gpu-memory-utilization 0.9`, `--max-model-len 32768`

### NIM
- モデルはコンテナイメージに含まれる（ホスト側マウント不要）
- NGC API キー認証が必要（`NGC_API_KEY` 環境変数）
- ワークスペースボリュームのマウントは不可（NIM 内部管理）

## 環境要件

- NVIDIA GPU + nvidia-container-toolkit
- Docker + Docker Compose
- モデルウェイト: `~/model_weights/` に配置（NIM を除く）

## ドキュメント

- `docs/thinking-mode.md`: Qwen3 Thinking モード
- `docs/tool-calling.md`: vLLM ツール呼び出しガイド
