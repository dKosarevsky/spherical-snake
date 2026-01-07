import base64
import os

from io import BytesIO

import numpy as np
import streamlit as st
import pygame

from PIL import Image

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
st.caption("Controls: use Left/Right arrow keys or the buttons below. Space restarts the game.")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⟵ Left", use_container_width=True, shortcut="Left"):
        st.session_state.left = True
        st.session_state.right = False
with col2:
    if st.button("⟳ Restart", use_container_width=True, shortcut="Space"):
        st.session_state.state = new_game(st.session_state.cfg)
with col3:
    if st.button("Right ⟶", use_container_width=True, shortcut="Right"):
        st.session_state.right = True
        st.session_state.left = False

with st.expander("Tuning"):
    st.session_state.cfg.step_rad = st.slider("Speed", 0.01, 0.12, st.session_state.cfg.step_rad, 0.005)
    st.session_state.cfg.turn_rad = st.slider("Turn", 0.02, 0.30, st.session_state.cfg.turn_rad, 0.01)

status_box = st.empty()
frame_box = st.empty()

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
pygame.init()

SIZE = 520
surf = pygame.Surface((SIZE, SIZE))


@st.fragment(run_every=0.033)  # ~30 FPS
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
    buf = BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    frame_box.markdown(
        f'<img src="data:image/png;base64,{encoded}" width="{SIZE}" height="{SIZE}" />',
        unsafe_allow_html=True,
    )
    status_box.caption(
        f"Score: {st.session_state.state.score} — {'ALIVE' if st.session_state.state.alive else 'GAME OVER'}")


loop()
