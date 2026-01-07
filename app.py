import base64
import os

from io import BytesIO

import numpy as np
import pygame
import streamlit as st

from PIL import Image, features

from game.core import GameConfig, new_game, step
from game.render import draw_frame

st.set_page_config(page_title="Spherical Snake (pygame+Streamlit)", layout="centered")

if "cfg" not in st.session_state:
    st.session_state.cfg = GameConfig()
if "state" not in st.session_state:
    st.session_state.state = new_game(st.session_state.cfg)
if "left" not in st.session_state:
    st.session_state.left = False
if "right" not in st.session_state:
    st.session_state.right = False

st.title("Spherical Snake")
st.caption("Controls: use Left/Right arrow keys. Space restarts the game.")

if st.button("⟳ Restart", use_container_width=True, shortcut="Space"):
    st.session_state.state = new_game(st.session_state.cfg)

with st.expander("Tuning"):
    st.session_state.cfg.step_rad = st.slider("Speed", 0.01, 0.12, st.session_state.cfg.step_rad, 0.005)
    st.session_state.cfg.turn_rad = st.slider("Turn", 0.02, 0.30, st.session_state.cfg.turn_rad, 0.01)

status_box = st.empty()
frame_box = st.empty()

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
pygame.init()

SIZE = 520
FRAME_BUFFER = BytesIO()
FRAME_FORMAT = "WEBP" if features.check("webp") else "JPEG"
FRAME_MIME = "image/webp" if FRAME_FORMAT == "WEBP" else "image/jpeg"
FRAME_SAVE_ARGS = {"quality": 80}
if FRAME_FORMAT == "JPEG":
    FRAME_SAVE_ARGS.update({"optimize": True})

surf = pygame.Surface((SIZE, SIZE))


@st.fragment(run_every=0.05)  # ~20 FPS
def loop():
    # 1) logic
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
    img = Image.fromarray(arr)
    FRAME_BUFFER.seek(0)
    FRAME_BUFFER.truncate(0)
    img.save(FRAME_BUFFER, format=FRAME_FORMAT, **FRAME_SAVE_ARGS)
    encoded = base64.b64encode(FRAME_BUFFER.getvalue()).decode("ascii")
    frame_box.markdown(
        f'<img src="data:{FRAME_MIME};base64,{encoded}" width="{SIZE}" height="{SIZE}" />',
        unsafe_allow_html=True,
    )
    status_box.caption(
        f"Score: {st.session_state.state.score} — {'ALIVE' if st.session_state.state.alive else 'GAME OVER'}"
    )


loop()

with st.container():
    left_col, right_col = st.columns(2)
    with left_col:
        if st.button("⟵ Left", use_container_width=True, shortcut="Left"):
            st.session_state.left = True
            st.session_state.right = False
    with right_col:
        if st.button("Right ⟶", use_container_width=True, shortcut="Right"):
            st.session_state.right = True
            st.session_state.left = False
