import os
import json
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Get the absolute directory of this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR)
CORS(app)

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/debate/speak', methods=['POST'])
def debate_speak():
    data = request.get_json()
    if not data:
        return jsonify({'ok': False, 'error': '无效请求'}), 400

    thinker = data.get('thinker', {})
    topic = data.get('topic', '')
    round_num = data.get('round', 1)
    history = data.get('history', [])
    api_key = data.get('api_key', '')

    if not api_key:
        return jsonify({'ok': False, 'error': '请先填写 API Key'}), 400

    if not thinker or not topic:
        return jsonify({'ok': False, 'error': '缺少 thinker 或 topic'}), 400

    # 构建对话历史
    messages = [
        {
            'role': 'system',
            'content': build_system_prompt(thinker, topic)
        }
    ]

    # 添加辩论历史
    if history:
        for h in history[-6:]:  # 最近6轮
            speaker = h.get('name', '某人')
            content = h.get('content', '')
            messages.append({
                'role': 'assistant' if h.get('thinker_id') == thinker.get('id') else 'user',
                'content': f"【{speaker}】{content}"
            })

    # 当前轮提示
    user_prompt = f"现在是第 {round_num} 轮辩论。请以{thinker.get('name', '')}的身份发言。"
    messages.append({'role': 'user', 'content': user_prompt})

    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': messages,
                'temperature': 0.85,
                'max_tokens': 300,
                'stream': False
            },
            timeout=30
        )

        if resp.status_code != 200:
            return jsonify({
                'ok': False,
                'error': f'DeepSeek API 错误: {resp.status_code} {resp.text[:200]}'
            }), 502

        result = resp.json()
        speech = result['choices'][0]['message']['content'].strip()

        # 清理多余的引号
        speech = speech.strip('"').strip("'")
        # 限制长度
        if len(speech) > 300:
            speech = speech[:297] + '⋯⋯'

        return jsonify({'ok': True, 'speech': speech})

    except requests.exceptions.Timeout:
        return jsonify({'ok': False, 'error': 'API 请求超时'}), 504
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


def build_system_prompt(thinker, topic):
    name = thinker.get('name', '思想家')
    school = thinker.get('school', '')
    core = thinker.get('core', '')
    era = thinker.get('era', '')
    region = thinker.get('region', 'cn')
    region_label = '中国' if region == 'cn' else '西方'
    quotes = thinker.get('quotes', [])[:5]
    persona = thinker.get('persona', {})
    anecdotes = thinker.get('anecdotes', [])

    prompt = f"""你是一位角色扮演助手。请完全代入以下思想家的身份，参与一场关于「{topic}」的辩论。

## 你的身份

- 姓名：{name}
- 时代：{era}（{region_label}）
- 学派/流派：{school}
- 核心思想：{core}

## 本次辩论的主题

「{topic}」

你的所有发言必须围绕这个主题展开。如果你谈论和这个主题无关的内容，你将被扣分。

## 说话风格

- 常用句式：{', '.join(persona.get('tics', [])[:5])}
- 典型情绪词：{', '.join(persona.get('emotions', [])[:5])}
- 辩论风格：喜欢{persona.get('openings', ['陈述观点'])[0]}、{persona.get('attacks', ['反驳'])[0]}

## 你的名言（可适当引用）

{chr(10).join(f'- {q}' for q in quotes)}

## 逸事（可偶尔提及）

{chr(10).join(anecdotes[:2]) if anecdotes else '无'}

## 重要约束（违反将扣分）

1. 你必须在每一轮发言中，结合「{topic}」这一主题展开论述。每句话都要围绕该主题。
2. 完全以{name}的第一人称口吻发言，不要用第三人称。
3. 字数控制在80-150字之间，精炼有力。
4. 适当引用该思想家标志性的名言或典故来支撑关于「{topic}」的观点。
5. 如果对手已经发言，可以针对性反驳对手关于该主题的观点。
6. 不要添加「{name}说：」这类前缀，直接发言。
7. 不要跑题——对跑题内容的惩罚非常严厉。"""
    return prompt


@app.route('/api/debate/fallback', methods=['POST'])
def fallback_speech():
    """备用：用前端模板生成（如果 API 不可用）"""
    return jsonify({'ok': True, 'fallback': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    print(f'AI 思想家辩论场 API 启动于 http://127.0.0.1:{port}')
    app.run(debug=debug, host='0.0.0.0', port=port)
