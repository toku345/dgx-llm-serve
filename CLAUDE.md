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

DGX Spark OEM機向け LLM 推論バックエンド（TensorRT-LLM, vLLM, NVIDIA NIM）を Docker Compose で管理するモノレポジトリ。

## ディレクトリ構造

```text
dgx-llm-serve/
├── backends/
│   ├── trtllm/    # TensorRT-LLM (Qwen3-FP4, Nemotron-NVFP4)
│   ├── vllm/      # vLLM (Qwen3-Coder, Qwen3.5, Nemotron, Nemotron-VL)
│   └── nim/       # NVIDIA NIM (DGX Spark 向け)
├── artifacts/     # ベンチマーク結果 (GenAI-Perf 出力)
├── docs/          # 共通ドキュメント
└── scripts/       # ユーティリティスクリプト
```

## 主要コマンド

### サーバー起動

```bash
# TensorRT-LLM (プロファイル選択)
cd backends/trtllm && docker compose --profile qwen up
cd backends/trtllm && docker compose --profile nemotron up
cd backends/trtllm && docker compose --profile multi up

# vLLM (プロファイル選択)
cd backends/vllm && docker compose --profile qwen up
cd backends/vllm && docker compose --profile qwen35 up
cd backends/vllm && docker compose --profile nemotron up
cd backends/vllm && docker compose --profile nemotron-vl up
cd backends/vllm && docker compose --profile multi up

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

# MODEL_NAME 例:
#   TRT-LLM:  nvidia/Qwen3-30B-A3B-FP4, nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4
#   vLLM:     Qwen/Qwen3-Coder-30B-A3B-Instruct, Qwen/Qwen3.5-35B-A3B-FP8
#             nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4, nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-NVFP4-QAD
#   NIM:      qwen3-32b-dgx-spark
```

### ベンチマーク

```bash
# GenAI-Perf によるベンチマーク（結果は artifacts/ に出力）
cd scripts && python benchmark.py
```

## バックエンド固有の注意事項

### TensorRT-LLM
- イメージ: `1.3.0rc4` (ARM64 対応)
- Nemotron: `--backend _autodeploy` + `compile_backend: torch-cudagraph` (Mamba SSM 互換)
- multi プロファイル: `qwen_multi.yaml` で KV キャッシュ制限必須（デフォルトだと OOM）
- SM120 `cudaErrorIllegalInstruction`: 1.3.0rc3+ で解消済み。Qwen の `compile_backend: torch-cudagraph` は削除済み
- Thinking モード: デフォルトで有効。`/no_think` をシステムプロンプトに追加で無効化
- クライアント側で `<think>...</think>` タグの除去が必要

### vLLM
- Qwen3.5-35B-A3B-FP8: `qwen35` プロファイル。`vllm/vllm-openai:cu130-nightly` 使用（NGC 26.01 は `qwen3_5_moe` 未対応、専用 cu130 ビルドは Triton/RMSNormGated バグあり）。`--reasoning-parser qwen3` で thinking を `reasoning_content` に分離。`--language-model-only` でビジョンエンコーダーを無効化（テキスト専用モード）。SM 12.1 では TRITON Fp8 MoE バックエンドが自動選択される
- ツール呼び出し対応（Qwen3-Coder）
- 内部プロンプト確認: `echo: true` パラメータを使用
- 設定パラメータ: `--gpu-memory-utilization 0.9`, `--max-model-len 32768`
- multi プロファイル: Qwen (25.11) + Nemotron (26.01) で異なるイメージ。ツール呼び出しは multi では無効
- Forward Compat 制約: ドライバ 580 では 26.01 (CUDA 13.1) コンテナは同時 1 つまで。26.01 × 2 は不可

### NIM
- モデル: `qwen/qwen3-32b-dgx-spark:1.1.0-variant`
- モデルはコンテナイメージに含まれる（ホスト側マウント不要）
- NGC API キー認証が必要（`NGC_API_KEY` 環境変数）
- ワークスペースボリュームのマウントは不可（NIM 内部管理）

## 環境要件

- ターゲット: DGX Spark OEM (GB10 SoC, ARM64, 128 GiB 統合メモリ)
- NVIDIA GPU + nvidia-container-toolkit
- Docker + Docker Compose
- Python (uv で管理。ベンチマークスクリプト用)
- モデルウェイト: `~/model_weights/` に配置（NIM を除く）

## 関連ドキュメント

- `docs/thinking-mode.md`: Qwen3 Thinking モード
- `docs/tool-calling.md`: vLLM ツール呼び出しガイド
