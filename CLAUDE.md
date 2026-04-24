# AGENTS.md / CLAUDE.md

このファイルは、このリポジトリで作業する **すべての AI コーディングエージェント** 向けの共通ガイドです。
（例: Claude Code, Codex, Cursor, Cline など）

## 基本方針（全エージェント共通）

- 変更は最小差分で行い、無関係なリファクタは避ける
- ユーザーが作成した既存変更は勝手に巻き戻さない
- 破壊的操作（`rm -rf`, `git reset --hard` など）は明示依頼がある場合のみ
- 実装後は、可能な範囲で検証コマンドを実行し、結果を報告する
- 不明点がある場合は、推測で進めすぎず短く具体的に確認する
- 新規依存や外部アクセスが必要な場合は、理由を明示して合意を取る

## プロジェクト概要

DGX Spark OEM 機向け LLM 推論バックエンド（vLLM）を Docker Compose で管理するモノレポジトリ。AI コーディングエージェント / Web サイト解析など多用途を **Qwen3.6-35B-A3B-FP8 単一モデル** でカバーする精選構成。

## ディレクトリ構造

```text
dgx-llm-serve/
├── backends/
│   └── vllm/      # vLLM (Qwen3.6-35B-A3B-FP8)
├── artifacts/     # ベンチマーク結果 (aiperf 出力)
├── docs/          # 共通ドキュメント
└── scripts/       # ユーティリティスクリプト
```

## 主要コマンド

### モデル重みダウンロード（初回のみ、約 36 GiB）

```bash
uv tool install "huggingface_hub[cli]"
hf download Qwen/Qwen3.6-35B-A3B-FP8 \
  --local-dir ~/model_weights/Qwen/Qwen3.6-35B-A3B-FP8
```

### サーバー起動

```bash
cd backends/vllm && docker compose --profile qwen36 up
```

### ヘルスチェック

```bash
curl http://localhost:8000/health
```

### API テスト

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.6-35B-A3B-FP8",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### ベンチマーク

```bash
# aiperf によるベンチマーク（結果は artifacts/ に出力）
uv run scripts/benchmark.py --model Qwen/Qwen3.6-35B-A3B-FP8
```

## バックエンド固有の注意事項（vLLM）

- **モデル**: `Qwen/Qwen3.6-35B-A3B-FP8` (MoE 35B total / 3B active, Apache 2.0, 2026-04-16 リリース)
- **イメージ**: `vllm/vllm-openai:v0.19.0-aarch64-cu130-ubuntu2404`（ARM64 / CUDA 13.0 / Ubuntu 24.04 フル修飾タグで明示 pin）
- **オプション**:
  - `--reasoning-parser qwen3`: `<think>...</think>` を `reasoning_content` フィールドに分離
  - `--enable-auto-tool-choice --tool-call-parser qwen3_coder`: OpenAI 互換の structured tool calls
  - `--max-model-len 131072` (128K): DGX Spark 単体の KV cache 制約内で最大
  - `--gpu-memory-utilization 0.8`: 重み ~36 GiB + KV cache + safety margin
- **SM 12.1 警告**: 起動ログに `cuda capability 12.1 が PyTorch 公式最大 12.0 を超過` 警告が出るが互換動作可能
- **スループット**: 実測 ~52 tok/s（decode, warm）。参考: Medium 報告 77.74 tok/s（別環境）
- **アーキテクチャ**: `Qwen3_5MoeForConditionalGeneration`（Qwen3.5 系を継承）

## 環境要件

- ターゲット: DGX Spark OEM (GB10 SoC, ARM64, 128 GiB 統合メモリ)
- NVIDIA GPU + nvidia-container-toolkit
- Docker + Docker Compose
- Python (uv で管理。ベンチマークスクリプト用)
- モデルウェイト: `~/model_weights/Qwen/Qwen3.6-35B-A3B-FP8/` に配置

## 関連ドキュメント

- `docs/thinking-mode.md`: Qwen3 Thinking モード
- `docs/tool-calling.md`: vLLM ツール呼び出しガイド
- `docs/plans/2026-04-24-model-curation-design.md`: モデル精選の設計書
- `docs/plans/2026-04-24-qwen36-smoke-test.md`: Smoke test 結果
