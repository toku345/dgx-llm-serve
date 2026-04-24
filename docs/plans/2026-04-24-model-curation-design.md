# DGX Spark OEM モデル精選設計書

- **作成日**: 2026-04-24
- **対象リポジトリ**: dgx-llm-serve
- **対象機体**: DGX Spark OEM (Lenovo ThinkStation PGX 等、GB10 SoC, 128 GiB unified, SM120 Blackwell, driver 580.126.09, ARM64)
- **ブランチ**: `feature/model-curation`

## 1. 背景と目的

### 目的
普段使いするモデル 1 本に精選し、未使用のバックエンド・プロファイルを全削除してリポジトリを最小化する。速度と品質のバランスが最良の構成に一本化する。

### 用途
1. **kakko-de**: AI コーディングエージェントのバックエンド
2. **briefer**: Web サイト解析アプリのバックエンド（当面テキストのみ、将来マルチモーダル）

両用途を単一モデルでまかない、同時起動は不要（切替運用）。

### 現状
- `backends/trtllm/` (qwen / nemotron / multi)
- `backends/vllm/` (qwen / qwen35 / nemotron / nemotron-vl / multi)
- `backends/nim/` (qwen3-32b-dgx-spark)
- 計 3 バックエンド、9 profile/yaml

### 選定結果
**Qwen/Qwen3.6-35B-A3B-FP8** (Apache 2.0, 2026-04-16 リリース) を vLLM で常用する。

**根拠**:
- MoE 35B 総 / 3B Active → GB10 273 GB/s 帯域で理論 91 tok/s、実測 **77.74 tok/s** (85% 効率)
- SWE-bench Verified **73.4%**（コーディング最高峰）
- Tool calling 成功率 97-100%（3.5 の 80% 台から改善）
- 262K context（128K から開始、KV cache との兼ね合いで調整）
- FP8 は Qwen 公式 variant、vLLM >=0.19.0 で対応
- NVFP4 は Qwen MoE で gibberish 報告あり (B200) のため見送り

## 2. アーキテクチャ（Before → After）

```
┌────────────────────────────────────────────────────────────────────────┐
│  Before（現状）                                                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  backends/trtllm/              backends/vllm/          backends/nim/    │
│  ┌──────────────────┐          ┌──────────────────┐    ┌─────────────┐  │
│  │ qwen.yaml        │          │ qwen     profile │    │ qwen3-32b   │  │
│  │ nano_v3.yaml     │          │ qwen35   profile │    │ -dgx-spark  │  │
│  │ qwen_multi.yaml  │          │ nemotron profile │    │             │  │
│  │ compose.yml      │          │ nemotron-vl  〃   │    │ compose.yml │  │
│  │ nginx.conf       │          │ multi    profile │    │             │  │
│  │                  │          │ compose.yml      │    │             │  │
│  │                  │          │ nginx.conf       │    │             │  │
│  │                  │          │ scripts/*        │    │             │  │
│  └──────────────────┘          └──────────────────┘    └─────────────┘  │
│                                                                         │
│  → 3 バックエンド、計 9 profile/yaml、3 Docker イメージ                   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ 精選（1 モデル / 1 バックエンドに絞る）
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  After（精選後）                                                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                          backends/vllm/                                 │
│                          ┌──────────────────────────────────┐           │
│                          │ qwen36 profile                   │           │
│                          │   └─ Qwen3.6-35B-A3B-FP8         │           │
│                          │      image: vllm/vllm-openai:    │           │
│                          │       v0.19.0-aarch64-cu130-      │           │
│                          │       ubuntu2404                  │           │
│                          │ compose.yml                      │           │
│                          └──────────────────────────────────┘           │
│                                                                         │
│  → 1 バックエンド、1 profile、用途:                                       │
│     ・kakko-de（コーディングエージェント）                                │
│     ・briefer（Web 解析、当面テキスト）                                   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

## 3. Phase 構成

ブランチ `feature/model-curation` 上で段階的にコミットし、ローカル smoke pass 確認後に単一 PR で提出。マージは Squash で commit 履歴を 1 つに集約。

| Phase | Commit | 内容 | Done 判定 |
|---|---|---|---|
| 0 | - | **前提準備**: Docker Hub でイメージタグ実在確認、モデル重みダウンロード | 両方完了 |
| 1 | commit 1 | `qwen36` profile 追加（既存は維持） | `docker compose config` valid、`docker compose --profile qwen36 up` 起動成功 |
| 2 | commit 2 | 実機 smoke test 実施、結果を `docs/plans/2026-04-24-qwen36-smoke-test.md` に記録 | 必須項目すべて pass |
| 3 | commit 3 | 既存削除 + ドキュメント更新（統合）| 残骸なし、ドキュメント整合 |
| Final | - | PR 作成・マージ | CI/セルフレビュー完了 |

### Phase 0 の前提準備（必須）

#### 0-A. イメージタグ実在確認
```bash
docker pull vllm/vllm-openai:v0.19.0-aarch64-cu130-ubuntu2404
```
失敗時は Docker Hub で最新 ARM64 / CUDA 13.0 タグを再調査し、本設計書を更新する。

#### 0-B. モデル重みダウンロード

**前提**: `huggingface_hub` CLI の導入

```bash
# 未導入の場合
uv tool install "huggingface_hub[cli]"

# Qwen3.6-35B-A3B-FP8 は現時点で public アクセス可能だが、認証推奨
huggingface-cli login    # 任意
```

**ダウンロード本体** (約 36 GiB、ネットワーク帯域次第で 30 分 〜 数時間):

```bash
huggingface-cli download Qwen/Qwen3.6-35B-A3B-FP8 \
  --local-dir ~/model_weights/Qwen/Qwen3.6-35B-A3B-FP8 \
  --local-dir-use-symlinks False
```

## 4. qwen36 profile 具体仕様

```yaml
vllm-qwen36:
  <<: *common
  image: vllm/vllm-openai:v0.19.0-aarch64-cu130-ubuntu2404
  profiles: ["qwen36"]
  command:
    - /app/model/Qwen/Qwen3.6-35B-A3B-FP8
    - --host
    - "0.0.0.0"
    - --port
    - "8000"
    - --served-model-name
    - Qwen/Qwen3.6-35B-A3B-FP8
    - --tensor-parallel-size
    - "1"
    - --gpu-memory-utilization
    - "0.8"
    - --max-model-len
    - "131072"
    - --max-num-seqs
    - "4"
    - --max-num-batched-tokens
    - "2048"
    - --dtype
    - auto
    - --kv-cache-dtype
    - auto
    - --reasoning-parser
    - qwen3
    - --enable-auto-tool-choice
    - --tool-call-parser
    - qwen3_coder
```

### オプション選定理由

| オプション | 値 | 理由 |
|---|---|---|
| `image` | `vllm/vllm-openai:v0.19.0-aarch64-cu130-ubuntu2404` | Codex 指摘 1: 曖昧な `v0.19+` や `latest` を避け明示 pin。ARM64 / CUDA 13.0 / Ubuntu 24.04 のフル修飾タグ |
| `--max-model-len` | `131072` (128K) | Qwen 公式 262K は TP=8 前提。DGX Spark 単体では 128K 推奨。OOM 回避 |
| `--gpu-memory-utilization` | `0.8` | モデル重み ~36 GiB + KV cache (128K × 4 seqs, FP8) + safety margin。128 GiB × 0.8 = 102 GiB 確保 |
| `--reasoning-parser qwen3` | 有効 | `<think>` を `reasoning_content` に分離。Qwen 公式 vLLM Recipe 準拠 |
| `--enable-auto-tool-choice` | 有効 | OpenAI 互換の structured tool calls を有効化 |
| `--tool-call-parser qwen3_coder` | 有効 | Qwen3 系推奨パーサ。kakko-de が依存する可能性が高い |
| `--language-model-only` | **除外** | Qwen3.6-35B-A3B は text-only モデル。vision encoder 非搭載のため不要 |
| `--enforce-eager` | **除外** | CUDA graphs 有効で 77.74 tok/s を達成するため |

## 5. Smoke test（Phase 2）

### 必須項目

| # | 項目 | 合格基準 | 注記 |
|---|---|---|---|
| 1 | `curl /health` | 200 OK | - |
| 2 | 短文 chat | レスポンス返却、`<think>` が `reasoning_content` に分離 | - |
| 3 | **長文 chat (50K token 入力)** | 50K+ トークンのプロンプトを投入し、応答生成が完了 | briefer 用途の現実検証 |
| 4 | 単発 tool call | structured `tool_calls` フィールドに出る | Codex 指摘 2 |
| 5 | **連続 tool call** | 2 回以上の連続 tool call が破綻しない | **Codex 指摘 2（致命可能性）** |
| 6 | スループット実測 | decode **60 tok/s 以上** (77.74 tok/s が既知実績) | curl レスポンスで手動計測 |
| 7 | `compose config` 検証 | Phase 1 commit の時点で valid | - |

### 任意項目

| # | 項目 | 内容 |
|---|---|---|
| 8 | aiperf 正式ベンチマーク | `uv run scripts/benchmark.py --model Qwen/Qwen3.6-35B-A3B-FP8` 実行、結果を `artifacts/` に保存（項目 6 の詳細化版） |

### 実施コマンド例

`docs/plans/2026-04-24-qwen36-smoke-test.md` 内で以下を順に実施し、結果（成功/失敗、ログ抜粋）を記録する。

```bash
# 項目 1: health check
curl -f http://localhost:8000/health

# 項目 2: 短文 chat + reasoning_content 分離確認
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.6-35B-A3B-FP8",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "max_tokens": 256
  }' | jq '.choices[0].message | {content, reasoning_content}'

# 項目 3: 長文 chat (50K token 入力)
# ダミー 50K token 相当の長文を用意（1 token ≈ 4 chars で約 200KB）
python3 -c "print('The quick brown fox jumps over the lazy dog. ' * 4500)" > /tmp/long_input.txt
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile txt /tmp/long_input.txt '{
    model: "Qwen/Qwen3.6-35B-A3B-FP8",
    messages: [{role: "user", content: ("以下を1文で要約してください: " + $txt)}],
    max_tokens: 200
  }')" | jq '.choices[0].message.content, .usage'

# 項目 4-5: tool call（単発・連続）
# 詳細は docs/tool-calling.md を参照。連続呼び出しは同一セッションで 2 回以上 tool call を誘発する
# プロンプト（例: 「東京の天気を取得してから、その温度を摂氏→華氏に変換」）で確認。

# 項目 6: スループット手動計測
# stream=true で decode トークン数と時間を計測
time curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.6-35B-A3B-FP8",
    "messages": [{"role": "user", "content": "Write a 500-word story about a robot."}],
    "max_tokens": 600,
    "stream": false
  }' | jq '.usage'
# completion_tokens / elapsed_seconds が 60 以上であること

# 項目 7: compose config 検証
docker compose --profile qwen36 config
```

### 失敗時の Rollback 手順

- **項目 4-5 失敗時**: vLLM issue #39056 が該当する可能性。以下の順で切り分け:
  1. `--reasoning-parser qwen3` を一時的に外して再試行
  2. それでも駄目なら `--tool-call-parser` の別値を試す
  3. 根本解決に至らない場合は Phase 3 に進まず、Qwen3.5 profile を残す判断で本設計を見直す

- **項目 1-3, 6-7 失敗時**:
  ```bash
  git reset --hard HEAD~1    # commit 1 を取り消し
  ```
  失敗ログは `docs/plans/2026-04-24-qwen36-smoke-test.md` に残し、原因究明後に再実施。

## 6. 削除対象

### ファイル / ディレクトリ

```
backends/trtllm/                     # ディレクトリごと削除
  ├─ compose.yml
  ├─ nginx.conf
  ├─ qwen.yaml
  ├─ qwen_multi.yaml
  ├─ nano_v3.yaml
  └─ README.md

backends/nim/                        # ディレクトリごと削除
  ├─ compose.yml
  └─ README.md

backends/vllm/scripts/vllm-up.sh     # 旧 Qwen3-Coder 用スクリプト
backends/vllm/scripts/               # 空になれば削除
backends/vllm/nginx.conf             # multi profile 用、不要に
```

### `backends/vllm/compose.yml` の編集

- `x-common` anchor は**残す**（qwen36 profile で参照）
- 削除するサービス: `vllm-qwen`, `vllm-qwen35`, `vllm-nemotron`, `vllm-multi-proxy`, `vllm-multi-qwen`, `vllm-multi-nemotron`, `vllm-nemotron-vl`
- 残すのは `vllm-qwen36` のみ

### 削除コマンド

本設計書の承認により、以下の破壊的操作を実施する:

```bash
git rm -r backends/trtllm/ backends/nim/
git rm backends/vllm/scripts/vllm-up.sh backends/vllm/nginx.conf
rmdir backends/vllm/scripts 2>/dev/null || true   # 空なら削除
# compose.yml は Edit で該当サービスを削除
```

### 更新対象ドキュメント

| ファイル | 更新内容 |
|---|---|
| `README.md` | バックエンド表 / クイックスタート / ドキュメントリンク |
| `CLAUDE.md` | ディレクトリ構造 / コマンド例 / バックエンド固有注意 |
| `AGENTS.md` | 同 CLAUDE.md |
| `backends/vllm/README.md` | profile 表 / multi 解説削除 / Forward Compat 節削除 |
| `docs/thinking-mode.md` | 対応バックエンド欄（TRT-LLM / multi を削除） |
| `docs/tool-calling.md` | モデル名を Qwen3.6-35B-A3B-FP8 に |
| `scripts/benchmark.py` | docstring 内モデル例示を更新 |

## 7. Done 判定基準

CLAUDE.md の必須ゲート準拠。Phase 別の受け入れ条件:

### Phase 0
- [ ] `docker pull vllm/vllm-openai:v0.19.0-aarch64-cu130-ubuntu2404` 成功
- [ ] `~/model_weights/Qwen/Qwen3.6-35B-A3B-FP8/` に重み配置完了

### Phase 1
- [ ] `docker compose config` が valid
- [ ] `docker compose --profile qwen36 up` で `/health` が 200 を返すまで起動
- [ ] 既存 profile は未変更（diff で確認）

### Phase 2
- [ ] Smoke test 必須項目 7 つすべて pass
- [ ] 結果を `docs/plans/2026-04-24-qwen36-smoke-test.md` に記録（失敗項目ゼロ）

### Phase 3
- [ ] 削除対象ファイル / ディレクトリがすべて削除済み
- [ ] 古いモデル名・バックエンド参照の残存チェック（両方とも 0 件想定、本設計書は除外）:
  ```bash
  # モデル名・profile 名の残存
  rg -w "trtllm|nemotron|nemotron-vl|qwen35|qwen3-coder" \
    -g '!docs/plans/' -g '*.md' -g '*.yml' -g '*.yaml' -g '*.sh' -g '*.py'
  # NIM 関連（NGC イメージパス等）
  rg "nvcr\.io/nim|\.cache/nim|backends/nim" -g '!docs/plans/'
  ```
- [ ] `docker compose --profile qwen36 up` が依然動作する

### Final（必須ゲート、常時適用）
- [ ] 動作検証済み: `docker compose --profile qwen36 up` で smoke pass
- [ ] 既存機能を破壊していない: `docker compose config` がエラーなし
- [ ] 差分が意図通り: `git diff main..HEAD` 確認済み
- [ ] シークレット未混入: `backends/nim/` 削除で NGC API キー参照も消滅

## 8. PR 情報

- **タイトル案**: `refactor: curate to single vLLM qwen36 profile (Qwen3.6-35B-A3B-FP8)`
- **ブランチ**: `feature/model-curation`
- **マージ方式**: Squash（commit 履歴を 1 つに集約）
- **PR 本文**: CLAUDE.md の「PR 作成手順」に従い、HEREDOC で Summary / Test plan を記載。Test plan には Phase 2 smoke test の結果サマリを含める。

## 9. 参考資料

- [Qwen/Qwen3.6-35B-A3B-FP8 model card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B-FP8)
- [Qwen3.5 & Qwen3.6 vLLM Recipe](https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen3.5.html)
- [vLLM releases](https://github.com/vllm-project/vllm/releases)
- [vLLM Qwen tool-call issue #39056](https://github.com/vllm-project/vllm/issues/39056)
- [Qwen3.6-35B-A3B on DGX Spark benchmark](https://allenkuo.medium.com/qwen3-6-35b-a3b-on-desktop-blackwell-the-first-time-vllm-beats-ollama-on-decode-f139f445f926)
- [NVIDIA Developer Forum: Qwen3.6-35B-A3B (and FP8) has landed](https://forums.developer.nvidia.com/t/qwen-qwen3-6-35b-a3b-and-fp8-has-landed/366822)
