"""Build a DeepSeek-style history export ZIP for import QA.

Usage: python scripts/make-fixture.py <output.zip>
"""

import io
import json
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

NOW = datetime.now(timezone.utc).replace(microsecond=0)


def iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def message(index, parent, role, text, moment, thinking=None):
    fragments = []
    if thinking:
        fragments.append({"type": "THINK", "content": thinking, "elapsed_secs": 2.4})
    fragments.append(
        {"type": "REQUEST" if role == "USER" else "RESPONSE", "content": text}
    )
    return {
        "id": index,
        "parent_id": parent,
        "role": role,
        "status": "FINISHED",
        "thinking_enabled": thinking is not None,
        "search_enabled": False,
        "accumulated_token_usage": index * 120,
        "inserted_at": iso(moment),
        "fragments": fragments,
    }


SESSIONS = [
    ("session-1e8fd278-ef04-4552-9476-70d65b0d487a", "给用户的温暖寄语", 1, 1),
    ("session-7b1c0a52-3f4d-4b21-9a33-1d2c5e6f7a80", "财帛离心禄解析", 1, 2),
    ("session-22f0c6b3-8a11-42d9-8f5e-2c4f1b6e9d33", "Dsh会话导入助手链接", 1, 3),
    ("session-9c3d5e17-6b28-4c04-9f61-3a7e2d8b1f55", "获取NPM_TOKEN步骤", 1, 5),
    ("session-4a8e1f60-2d35-4b77-8c0e-6f1a9b3d2c44", "Gemini讨论热度低原因", 2, 9),
    ("session-6f2b9d41-0c58-4e13-a7b2-8d5f3e1c0a66", "Blender全能创作力", 34, 3),
]

# 额外填充会话：让导入耗时更接近真实导出包，便于观察进度。
for index in range(24):
    SESSIONS.append(
        (
            f"session-{index:02d}42a1b-77c9-4d10-8e2f-{index:012d}",
            f"历史对话 {index + 1}",
            2 + index % 5,
            1 + index % 9,
        )
    )

CONVERSATIONS = [
    ("你好", "你好！我是 DeepSleep，很高兴见到你。今天想聊点什么？"),
    ("给我一句温暖的话", "愿你今天遇到的所有事，都比预想的顺一点点。"),
    (
        "财帛离心禄是什么意思",
        "「离心禄」在紫微斗数的四化体系里，指的是禄星离开原本的宫位，力量分散到对宫。\n"
        "它本身不是坏事，代表财源需要「动」才能到手：跑动、外派、跨区域、线上业务都比死守一处更顺。",
    ),
    ("Dsh会话导入助手链接怎么用", "在数据管理里点「从链接导入」，把官网给出的下载链接粘进去就行。"),
    ("NPM_TOKEN 在哪拿", "登录 npmjs 网站，进入 Access Tokens 页面新建 Classic Token。"),
    ("Gemini 最近讨论度为什么低", "主要是产品节奏和渠道差异，以及中文社区的内容供给偏少。"),
    ("Blender 能做什么", "建模、绑定、动画、渲染、合成，甚至剪辑和 2D 绘制都能覆盖。"),
]


def build(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    index = []
    pending = []
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps({"export_format_version": 3}, ensure_ascii=False))
        archive.writestr("user.json", json.dumps({"name": "创软"}, ensure_ascii=False))

        for order, (session_id, title, days, hours) in enumerate(SESSIONS):
            created = NOW - timedelta(days=days, hours=hours)
            messages = []
            parent = None
            for step, (question, answer) in enumerate(CONVERSATIONS):
                moment = created + timedelta(minutes=step * 3)
                user_id = len(messages) + 1
                messages.append(message(user_id, parent, "USER", question, moment))
                answer_id = len(messages) + 1
                messages.append(
                    message(
                        answer_id,
                        user_id,
                        "ASSISTANT",
                        answer,
                        moment + timedelta(seconds=40),
                        thinking="先确认问题边界，再给出结论。" if step == 2 else None,
                    )
                )
                parent = answer_id
            if order == 0:
                # 附带一张图片，验证附件导入路径
                image = Image.new("RGB", (96, 96), (77, 107, 254))
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                pending.append(
                    (
                        f"chat_sessions/{session_id}_files/2f7d1c88-1111-4a2b-9c33-0a1b2c3d4e5f_blue.png",
                        buffer.getvalue(),
                    )
                )
                messages[0]["fragments"].insert(
                    0,
                    {
                        "type": "FILE",
                        "files": [
                            {
                                "id": "2f7d1c88-1111-4a2b-9c33-0a1b2c3d4e5f",
                                "file_name": "blue.png",
                                "file_size": buffer.tell(),
                                "token_usage": None,
                                "inserted_at": iso(created),
                                "export_path": f"chat_sessions/{session_id}_files/2f7d1c88-1111-4a2b-9c33-0a1b2c3d4e5f_blue.png",
                                "is_image": True,
                                "width": 96,
                                "height": 96,
                            }
                        ],
                    },
                )
            payload = {
                "id": session_id,
                "title": title,
                "pinned": False,
                "current_message_id": messages[-1]["id"],
                "inserted_at": iso(created),
                "updated_at": iso(created + timedelta(minutes=len(messages))),
                "messages": messages,
            }
            archive.writestr(
                f"chat_sessions/{session_id}.json", json.dumps(payload, ensure_ascii=False)
            )
            index.append(
                {
                    "id": session_id,
                    "title": title,
                    "pinned": False,
                    "message_count": len(messages),
                    "inserted_at": iso(created),
                    "updated_at": iso(created + timedelta(minutes=len(messages))),
                }
            )
        archive.writestr("chat_session_index.json", json.dumps(index, ensure_ascii=False))
        # 产物顺序固定：图片一律排在索引之后。
        for name, data in pending:
            archive.writestr(name, data)
    print(f"wrote {target} ({target.stat().st_size} bytes, {len(index)} sessions)")


build(Path(sys.argv[1]))
