# vLLM ツール呼び出しガイド

vLLM でツール呼び出し（Function Calling）を使用する際の設定と、内部プロンプトのデバッグ方法をまとめる。

## ツール呼び出しの有効化

### vLLM サーバー起動コマンド

```bash
vllm serve Qwen/Qwen3-Coder-8B-Instruct \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder
```

### Docker Compose 設定例

```yaml
services:
  vllm:
    image: nvcr.io/nvidia/vllm:26.01-py3
    command: >
      vllm serve Qwen/Qwen3-Coder-8B-Instruct
      --enable-auto-tool-choice
      --tool-call-parser hermes
```

---

## 内部プロンプトの確認方法

### 方法1: echo=true パラメータ（推奨）

API リクエストに `echo: true` を追加することで、`prompt_logprobs` フィールドに内部プロンプトの各トークンが返却される。

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    "messages": [{"role": "user", "content": "What is the weather in Tokyo?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string", "description": "City name"}
          },
          "required": ["location"]
        }
      }
    }],
    "tool_choice": "auto",
    "echo": true
  }' > /tmp/echo_response.json
```

内部プロンプトの整形表示:

```bash
python3 -c "
import json
with open('/tmp/echo_response.json') as f:
    data = json.load(f)
tokens = []
for item in data['prompt_logprobs']:
    if item is None:
        continue
    for key, value in item.items():
        if 'decoded_token' in value:
            tokens.append(value['decoded_token'])
print(''.join(tokens))
"
```

### 方法2: apply_chat_template でオフライン確認

vLLM を起動せずにローカルでプロンプトを確認できる。

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Coder-8B-Instruct")

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's the weather in Tokyo?"}
]

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather information",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"]
            }
        }
    }
]

formatted_prompt = tokenizer.apply_chat_template(
    messages,
    tools=tools,
    tokenize=False,
    add_generation_prompt=True
)
print(formatted_prompt)
```

### 方法3: /tokenize エンドポイント

```bash
curl -X POST http://localhost:8000/tokenize \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Qwen/Qwen3-Coder-8B-Instruct",
        "messages": [
            {"role": "user", "content": "What is the weather in Tokyo?"}
        ]
    }'
```

### 方法4: chat_template を直接確認

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Coder-8B-Instruct")
print(tokenizer.chat_template)
```

---

## 方法比較

| 方法 | vLLM起動 | 難易度 | 精度 | 用途 |
|------|----------|--------|------|------|
| `echo=true` | 必要 | 低 | 高 | ランタイムデバッグ |
| `apply_chat_template` | 不要 | 低 | 高 | 開発時の確認 |
| `/tokenize` API | 必要 | 中 | 高 | API経由での確認 |
| chat_template直接確認 | 不要 | 低 | - | テンプレート理解 |

---

## 補足: デバッグログ環境変数

以下の環境変数は内部プロンプトの出力には対応していない:

| 環境変数 | 結果 |
|---------|------|
| `VLLM_LOGGING_LEVEL=DEBUG` | バッチ実行情報、エンジン状態等は出力される |
| `VLLM_DEBUG_LOG_API_SERVER_RESPONSE=TRUE` | API レスポンスのログ出力用 |

**内部プロンプトの確認には方法1（echo=true）または方法2（apply_chat_template）を使用すること。**

---

## ツール呼び出しフォーマット

Qwen3-Coder は以下の形式でツール呼び出しを出力:

```
<tool_call>
{"name": "get_weather", "arguments": {"city": "Tokyo"}}
</tool_call>
```

---

## 参考リンク

- [vLLM Tool Calling ドキュメント](https://docs.vllm.ai/en/latest/features/tool_calling/)
- [vLLM 環境変数一覧](https://docs.vllm.ai/en/stable/configuration/env_vars/)
- [Qwen Function Calling ガイド](https://qwen.readthedocs.io/en/latest/framework/function_call.html)
- [HuggingFace Chat Templates ドキュメント](https://huggingface.co/docs/transformers/en/chat_templating)
