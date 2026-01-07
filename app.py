import base64
import math
import os
from io import BytesIO

import numpy as np
import pygame
import streamlit as st
from PIL import Image

from game.core import GameConfig, apple_guidance, new_game, step
from game.render import draw_frame


def apple_lat_lon(vec: np.ndarray | tuple[float, float, float]) -> tuple[float, float]:
    lat = math.degrees(math.asin(max(-1.0, min(1.0, vec[2]))))
    lon = math.degrees(math.atan2(vec[1], vec[0]))
    return lat, lon


st.set_page_config(page_title="Spherical Snake (pygame+Streamlit)", layout="centered")

if "cfg" not in st.session_state:
    st.session_state.cfg = GameConfig()
if "state" not in st.session_state:
    st.session_state.state = new_game(st.session_state.cfg)
if "left" not in st.session_state:
    st.session_state.left = False
if "right" not in st.session_state:
    st.session_state.right = False
if "auto_steer" not in st.session_state:
    st.session_state.auto_steer = False
if "auto_assist_deg" not in st.session_state:
    st.session_state.auto_assist_deg = 12.0

st.title("Spherical Snake")
st.caption("Controls: use Left/Right arrow keys. Space restarts the game.")

if st.button("⟳ Restart", use_container_width=True, shortcut="Space"):
    st.session_state.state = new_game(st.session_state.cfg)

with st.expander("Tuning"):
    st.session_state.cfg.step_rad = st.slider("Speed", 0.01, 0.12, st.session_state.cfg.step_rad, 0.005)
    st.session_state.cfg.turn_rad = st.slider("Turn", 0.02, 0.80, st.session_state.cfg.turn_rad, 0.01)
    st.checkbox(
        "Auto steer toward apple when idle",
        key="auto_steer",
        help="Automatically tap Left/Right to point the head toward the apple whenever no manual input is active.",
    )
    st.slider(
        "Auto steer sensitivity (°)",
        1.0,
        45.0,
        st.session_state.auto_assist_deg,
        key="auto_assist_deg",
        help="Minimum angular offset before auto steering kicks in.",
    )

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
pygame.init()

try:
    rt = st.runtime.get_instance()
    if rt and hasattr(rt, "media_file_mgr"):
        rt.media_file_mgr.remove_orphaned_files = lambda *_, **__: None
except Exception:
    pass

SIZE = 520
surf = pygame.Surface((SIZE, SIZE))


@st.fragment(run_every=0.05)  # ~20 FPS
def loop():
    assist_threshold = math.radians(st.session_state.get("auto_assist_deg", 12.0))
    guidance_before = apple_guidance(st.session_state.state)
    if (
            st.session_state.get("auto_steer")
            and guidance_before is not None
            and not st.session_state.left
            and not st.session_state.right
    ):
        offset, turn_dir = guidance_before
        if offset > assist_threshold:
            if turn_dir > 0:
                st.session_state.left = True
                st.session_state.right = False
            elif turn_dir < 0:
                st.session_state.right = True
                st.session_state.left = False

    step(
        st.session_state.state,
        st.session_state.cfg,
        left=st.session_state.left,
        right=st.session_state.right,
    )
    # buttons edge-trigger
    st.session_state.left = False
    st.session_state.right = False

    # 2) render
    draw_frame(surf, st.session_state.state)
    arr = pygame.surfarray.array3d(surf)  # (w,h,3)
    arr = np.transpose(arr, (1, 0, 2))  # (h,w,3)
    img_html = Image.fromarray(arr)
    buf = BytesIO()
    img_html.save(buf, format="JPEG", quality=90, optimize=False)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    st.markdown(
        f'<img src="data:image/jpeg;base64,{encoded}" width="{SIZE}" height="{SIZE}" style="display:block;margin:auto;border-radius:12px;background:#050507;" />',
        unsafe_allow_html=True,
    )
    guidance_after = apple_guidance(st.session_state.state)
    lat, lon = apple_lat_lon(st.session_state.state.apple)
    status_parts = [
        f"Score: {st.session_state.state.score} — {'ALIVE' if st.session_state.state.alive else 'GAME OVER'}",
        f"Apple lat {lat:.1f}°, lon {lon:.1f}°",
    ]
    if guidance_after:
        deg_off = math.degrees(guidance_after[0])
        if deg_off < 0.2:
            status_parts.append("Offset: on target")
        else:
            hint = "LEFT" if guidance_after[1] > 0 else "RIGHT"
            status_parts.append(f"Offset: {deg_off:.1f}° {hint}")
    st.caption(" | ".join(status_parts))


loop()


@st.fragment
def controls() -> None:
    cols = st.columns(2, gap="small")
    with cols[0]:
        if st.button("←", use_container_width=True, help="Turn left"):
            st.session_state.left = True
            st.session_state.right = False
    with cols[1]:
        if st.button("→", use_container_width=True, help="Turn right"):
            st.session_state.right = True
            st.session_state.left = False


controls()
