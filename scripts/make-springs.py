"""Generate CSS linear() spring curves from (stiffness, damping) pairs.

Usage: python scripts/make-springs.py
"""

import math


def settle_time(stiffness: float, damping: float, tolerance: float = 0.002) -> float:
    omega = math.sqrt(stiffness)
    zeta = damping / (2 * omega)
    if zeta >= 1:
        return 5.2 / omega
    decay = zeta * omega
    return math.log(1 / tolerance) / decay


def sample(stiffness: float, damping: float, steps: int = 14):
    omega = math.sqrt(stiffness)
    zeta = damping / (2 * omega)
    duration = settle_time(stiffness, damping)
    if zeta < 1:
        omega_d = omega * math.sqrt(1 - zeta * zeta)

        def value(t: float) -> float:
            decay = math.exp(-zeta * omega * t)
            return 1 - decay * (
                math.cos(omega_d * t) + (zeta * omega / omega_d) * math.sin(omega_d * t)
            )

    else:
        def value(t: float) -> float:
            return 1 - math.exp(-omega * t) * (1 + omega * t)

    points = []
    for index in range(steps + 1):
        ratio = index / steps
        t = duration * ratio
        # 最后一帧必须精确落到 1，否则过渡结束时元素停在偏移位置
        value_ = 1.0 if index == steps else value(t)
        points.append((round(ratio * 100, 1), round(value_, 4)))
    return duration, points


PRESETS = {
    # 名称: (刚度, 阻尼)  —— 阻尼比 ζ 决定过冲幅度
    'spring-soft': (150, 26),     # ζ≈1.06 临界阻尼，进度条这类不该过冲的
    'spring-default': (200, 22),  # ζ≈0.78 默认抽屉/页面推入
    'spring-pop': (260, 20),      # ζ≈0.62 菜单、弹层，明显一点的回弹
    'spring-snap': (400, 30),     # ζ≈0.75 按压反馈，快而脆
    'spring-back': (180, 18),     # ζ≈0.67 手势回弹，松手后带一点甩尾
}

print('/* 由 scripts/make-springs.py 生成：阻尼弹簧的阶跃响应采样 */')
lines = ['/* 由 scripts/make-springs.py 生成：阻尼弹簧的阶跃响应采样。',
         '   改参数请改脚本后重新生成，不要手改曲线。 */',
         ':root {']
for name, (stiffness, damping) in PRESETS.items():
    duration, points = sample(stiffness, damping)
    stops = ', '.join(
        f'{value}' if percent == 0 else f'{value} {percent}%' for percent, value in points
    )
    zeta = damping / (2 * math.sqrt(stiffness))
    lines.append(f'  /* ζ={zeta:.2f} settle≈{duration * 1000:.0f}ms */')
    lines.append(f'  --{name}: {duration * 1000:.0f}ms linear({stops});')
lines.append('}')
text = '\n'.join(lines) + '\n'
from pathlib import Path

Path('src/app/motion.css').write_text(text, encoding='utf-8')
print(text)
