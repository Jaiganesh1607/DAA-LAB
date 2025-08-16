import html
import streamlit as st

# ------------------------------
# 1) Algorithm (ported as-is)
# ------------------------------
def naive_search_steps(text, pattern):
    """
    Build the same sequence of steps as the Tkinter generator, but as a list.
    Each step is a dict:
      - text_idx
      - pattern_idx
      - shift
      - match: None (about to compare), False (mismatch), True (full match)
      - found_indices: [] or [i]
    """
    n = len(text)
    m = len(pattern)
    steps = []

    if m == 0 or n < m:
        return steps

    for i in range(n - m + 1):
        for j in range(m):
            # Before comparison
            steps.append({
                'text_idx': i + j,
                'pattern_idx': j,
                'shift': i,
                'match': None,
                'found_indices': []
            })
            if text[i + j] != pattern[j]:
                # Mismatch
                steps.append({
                    'text_idx': i + j,
                    'pattern_idx': j,
                    'shift': i,
                    'match': False,
                    'found_indices': []
                })
                break
        else:
            # Full match
            steps.append({
                'text_idx': i + m - 1,
                'pattern_idx': m - 1,
                'shift': i,
                'match': True,
                'found_indices': [i]
            })
    return steps


# ------------------------------
# 2) State helpers
# ------------------------------
def init_state():
    st.session_state.setdefault("text", "AABAACAADAABAABA")
    st.session_state.setdefault("pattern", "AABA")
    st.session_state.setdefault("steps", [])
    st.session_state.setdefault("step_idx", None)   # None -> not started; -1 -> initial layout; >=0 -> in steps
    st.session_state.setdefault("found_indices", [])
    st.session_state.setdefault("started", False)
    st.session_state.setdefault("complete", False)

def reset_state():
    st.session_state["steps"] = []
    st.session_state["step_idx"] = None
    st.session_state["found_indices"] = []
    st.session_state["started"] = False
    st.session_state["complete"] = False


# ------------------------------
# 3) Rendering (HTML/CSS grid)
# ------------------------------
CSS = """
<style>
:root {
  --box-size: 40px;
  --gap: 10px;
}
.wrapper {
  background: #2c3e50;
  padding: 16px;
  border-radius: 12px;
}
.grid {
  display: grid;
  column-gap: var(--gap);
  row-gap: 8px;
  justify-content: center;
}
.char {
  width: var(--box-size);
  height: var(--box-size);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-family: Consolas, monospace;
  font-weight: 700;
  background: #ecf0f1;   /* default */
  color: #34495e;
  user-select: none;
}
.char.comparing { background: #f1c40f; }  /* yellow */
.char.mismatch  { background: #e74c3c; color: #ffffff; }  /* red */
.char.match     { background: #2ecc71; color: #ffffff; }  /* green */
.char.found     { background: #3498db; color: #ffffff; }  /* blue */

.label {
  text-align: center;
  font-family: Consolas, monospace;
  font-size: 12px;
  color: #ffffff;
}

.legend {
  display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
}
.legend .dot {
  width: 16px; height: 16px; border-radius: 4px; display: inline-block; margin-right: 6px;
}
.dot-default  { background: #ecf0f1; border: 1px solid #bdc3c7; }
.dot-compare  { background: #f1c40f; }
.dot-mismatch { background: #e74c3c; }
.dot-match    { background: #2ecc71; }
.dot-found    { background: #3498db; }
</style>
"""

def render_visual(text, pattern, step, found_indices_so_far):
    """
    Build an HTML grid similar to the Tkinter canvas visualization.

    Rows:
      1) Pattern indices
      2) Pattern boxes (shifted)
      3) Text boxes
      4) Text indices
    """
    n = len(text)
    m = len(pattern)

    # Determine current step details
    if step is None:
        shift = 0
        match_status = None
        text_idx = None
        pattern_idx = None
        step_found = []
    else:
        shift = step["shift"]
        match_status = step["match"]
        text_idx = step["text_idx"]
        pattern_idx = step["pattern_idx"]
        step_found = step["found_indices"][:]  # [] or [i]

    # Build sets for quick highlighting of previously found segments
    previously_found_positions = set()
    for fi in found_indices_so_far:
        for k in range(m):
            previously_found_positions.add(fi + k)

    # If the current step is a "full match", we want the *current* match to be green,
    # even if previously found matches exist.
    current_match_positions = set()
    if match_status is True and step_found:
        fi = step_found[0]
        for k in range(m):
            current_match_positions.add(fi + k)

    # HTML begin
    grid_cols = n
    html_parts = []
    html_parts.append('<div class="wrapper">')
    html_parts.append(f'<div class="grid" style="grid-template-columns: repeat({grid_cols}, var(--box-size));">')

    # Row 1: Pattern index labels (shifted)
    for i in range(m):
        col = shift + i + 1
        if 1 <= col <= n:
            html_parts.append(f'<div class="label" style="grid-row:1; grid-column:{col};">{i}</div>')

    # Row 2: Pattern boxes
    for i, ch in enumerate(pattern):
        col = shift + i + 1
        if not (1 <= col <= n):
            continue
        classes = ["char"]
        if match_status is None and i == pattern_idx:
            classes.append("comparing")
        elif match_status is False and i == pattern_idx:
            classes.append("mismatch")
        elif match_status is True:
            classes.append("match")
        safe_ch = html.escape(ch)
        html_parts.append(
            f'<div class="{" ".join(classes)}" style="grid-row:2; grid-column:{col};">{safe_ch}</div>'
        )

    # Row 3: Text boxes
    for i, ch in enumerate(text):
        classes = ["char"]
        # Previously found (blue), unless current step is marking a new full match at this position (green)
        if i in previously_found_positions:
            classes.append("found")
        # Override with current step highlight if applicable
        if match_status is None and i == text_idx:
            classes = ["char", "comparing"]
        elif match_status is False and i == text_idx:
            classes = ["char", "mismatch"]
        elif match_status is True and i in current_match_positions:
            classes = ["char", "match"]

        safe_ch = html.escape(ch)
        html_parts.append(
            f'<div class="{" ".join(classes)}" style="grid-row:3; grid-column:{i+1};">{safe_ch}</div>'
        )

    # Row 4: Text index labels
    for i in range(n):
        html_parts.append(f'<div class="label" style="grid-row:4; grid-column:{i+1};">{i}</div>')

    html_parts.append('</div></div>')  # grid + wrapper
    return "\n".join(html_parts)


def status_text(step, found_indices, pattern_len):
    if step is None:
        return "Ready. Press 'Next Step' to begin comparison."
    shift = step["shift"]
    t = step["text_idx"]
    p = step["pattern_idx"]
    m = step["match"]
    if m is None:
        return f"Shifting pattern by {shift}. Comparing pattern[{p}] with text[{t}]."
    elif m is False:
        return f"Mismatch at text[{t}] and pattern[{p}]. Shifting pattern."
    else:
        idx = step["found_indices"][0]
        return f"Pattern found at index {idx}! Press 'Next Step' to continue search."


# ------------------------------
# 4) UI
# ------------------------------
st.set_page_config(page_title="Naive String Search Visualizer", page_icon="🔎", layout="wide")
init_state()
st.markdown(CSS, unsafe_allow_html=True)

st.title("Naive String Search Visualizer")

# Inputs
with st.container():
    c1, c2 = st.columns([2, 1])
    with c1:
        st.session_state.text = st.text_input("Text", value=st.session_state.text, key="text_input")
    with c2:
        st.session_state.pattern = st.text_input("Pattern", value=st.session_state.pattern, key="pattern_input")

# Controls
col_start, col_next, col_reset = st.columns([1, 1, 1])
with col_start:
    if st.button("Start Search", use_container_width=True):
        text = st.session_state.text_input
        pattern = st.session_state.pattern_input
        # Validation similar to Tk
        if not text or not pattern:
            st.error("Text and Pattern cannot be empty.")
        elif len(pattern) > len(text):
            st.error("Pattern cannot be longer than the text.")
        else:
            st.session_state.steps = naive_search_steps(text, pattern)
            st.session_state.found_indices = []
            st.session_state.step_idx = -1  # show initial layout first
            st.session_state.started = True
            st.session_state.complete = False

with col_next:
    disabled_next = not st.session_state.started or st.session_state.complete
    if st.button("Next Step", use_container_width=True, disabled=disabled_next):
        if st.session_state.step_idx is None:
            # not started
            pass
        else:
            # move from initial (-1) to first step, or advance
            if st.session_state.step_idx < len(st.session_state.steps) - 1:
                st.session_state.step_idx += 1
                step = st.session_state.steps[st.session_state.step_idx]
                if step["match"] is True and step["found_indices"]:
                    st.session_state.found_indices.extend(step["found_indices"])
            else:
                st.session_state.complete = True

with col_reset:
    if st.button("Reset", use_container_width=True):
        reset_state()
        # keep convenient defaults
        st.session_state.text = "AABAACAADAABAABA"
        st.session_state.pattern = "AABA"

st.divider()

# Visualization
text = st.session_state.text_input if "text_input" in st.session_state else st.session_state.text
pattern = st.session_state.pattern_input if "pattern_input" in st.session_state else st.session_state.pattern

current_step = None
if st.session_state.started:
    if st.session_state.step_idx == -1:
        current_step = None  # initial layout
    elif 0 <= st.session_state.step_idx < len(st.session_state.steps):
        current_step = st.session_state.steps[st.session_state.step_idx]

html_vis = render_visual(text, pattern, current_step, st.session_state.found_indices)
st.markdown(html_vis, unsafe_allow_html=True)

# Status + completion
if not st.session_state.started:
    st.info("Enter text and pattern, then press **Start Search**.")
else:
    st.caption(status_text(current_step, st.session_state.found_indices, len(pattern)))

    # When finished, mirror Tkinter's summary
    if st.session_state.step_idx is not None and st.session_state.step_idx >= (len(st.session_state.steps) - 1):
        if not st.session_state.complete:
            # user just arrived at last step; allow one more click to set complete
            pass
        else:
            if st.session_state.found_indices:
                st.success(f"Search complete. Pattern found at indices: {st.session_state.found_indices}")
            else:
                st.warning("Search complete. Pattern not found.")
            st.caption("Press **Reset** to start again.")

# Legend (matches your Tk colors)
with st.expander("Legend", expanded=False):
    st.markdown(
        """
        <div class="legend">
          <span><i class="dot dot-default"></i> Default</span>
          <span><i class="dot dot-compare"></i> Comparing</span>
          <span><i class="dot dot-mismatch"></i> Mismatch</span>
          <span><i class="dot dot-match"></i> Current Full Match</span>
          <span><i class="dot dot-found"></i> Previously Found</span>
        </div>
        """,
        unsafe_allow_html=True
    )
