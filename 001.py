import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from itertools import permutations
import math

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="生產排程甘特圖",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans TC', sans-serif;
}

.stApp {
    background: #0f1117;
    color: #e8eaf0;
}

/* Header */
.main-header {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%);
    border-bottom: 1px solid #2a3040;
    padding: 1.5rem 0 1rem 0;
    margin-bottom: 1.5rem;
    text-align: center;
}
.main-header h1 {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    background: linear-gradient(90deg, #4fc3f7, #81d4fa, #b3e5fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.main-header p {
    color: #7986a3;
    font-size: 0.85rem;
    margin-top: 0.3rem;
    letter-spacing: 0.08em;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #1a1f2e;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #2a3040;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #7986a3;
    font-weight: 500;
    font-size: 0.95rem;
    padding: 0.5rem 1.5rem;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1565c0, #1976d2) !important;
    color: white !important;
}

/* Metric Cards */
.metric-card {
    background: #1a1f2e;
    border: 1px solid #2a3040;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #4fc3f7; }
.metric-card .label {
    font-size: 0.75rem;
    color: #7986a3;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.metric-card .value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: #4fc3f7;
}
.metric-card .unit {
    font-size: 0.75rem;
    color: #546e7a;
    margin-top: 0.1rem;
}

/* Result Table */
.result-table {
    background: #1a1f2e;
    border: 1px solid #2a3040;
    border-radius: 12px;
    padding: 1rem;
    margin-top: 1rem;
}

/* Input Section */
.stDataEditor, .stNumberInput, .stSelectbox {
    background: #1a1f2e !important;
}

/* Divider */
.section-title {
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #546e7a;
    border-left: 3px solid #1976d2;
    padding-left: 0.7rem;
    margin: 1.2rem 0 0.8rem 0;
}

/* Algorithm badge */
.algo-badge {
    display: inline-block;
    background: linear-gradient(135deg, #0d47a1, #1565c0);
    color: #90caf9;
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.08em;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    border: 1px solid #1976d2;
    margin-left: 0.5rem;
}

/* Info box */
.info-box {
    background: #0d2137;
    border: 1px solid #1565c0;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    color: #90caf9;
    font-size: 0.82rem;
    margin-bottom: 1rem;
    line-height: 1.6;
}

/* Late job highlight */
.late-badge {
    background: #b71c1c;
    color: #ffcdd2;
    font-size: 0.7rem;
    padding: 0.1rem 0.5rem;
    border-radius: 10px;
    margin-left: 0.4rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏭 生產排程甘特圖</h1>
    <p>PRODUCTION SCHEDULING VISUALIZATION SYSTEM</p>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
#   ALGORITHMS
# ════════════════════════════════════════════════════════════════════

def schedule_single_machine(jobs_df, algorithm):
    """Single machine scheduling algorithms."""
    jobs = jobs_df.copy().reset_index(drop=True)
    jobs["job_id"] = [f"J{i+1}" for i in range(len(jobs))]

    if algorithm == "SPT（最短加工時間）":
        jobs = jobs.sort_values("加工時間").reset_index(drop=True)
    elif algorithm == "EDD（最早到期日）":
        jobs = jobs.sort_values("到期時間").reset_index(drop=True)
    elif algorithm == "FCFS（先到先服務）":
        pass  # keep original order
    elif algorithm == "LPT（最長加工時間）":
        jobs = jobs.sort_values("加工時間", ascending=False).reset_index(drop=True)
    elif algorithm == "最小化最大延遲（Moore）":
        jobs = _moore_algorithm(jobs)

    # Compute schedule
    schedule = []
    time = 0
    for _, row in jobs.iterrows():
        start = time
        end = time + row["加工時間"]
        late = max(0, end - row["到期時間"])
        schedule.append({
            "工作": row["job_id"],
            "開始時間": start,
            "結束時間": end,
            "加工時間": row["加工時間"],
            "到期時間": row["到期時間"],
            "延遲": late,
            "是否延遲": late > 0,
        })
        time = end
    return pd.DataFrame(schedule)


def _moore_algorithm(jobs):
    """Moore's algorithm to minimize number of late jobs."""
    jobs = jobs.sort_values("到期時間").reset_index(drop=True)
    scheduled = []
    rejected = []
    t = 0
    for _, row in jobs.iterrows():
        scheduled.append(row)
        t += row["加工時間"]
        if t > row["到期時間"]:
            # Remove the job with longest processing time from scheduled
            # Use list position index, not DataFrame index
            proc_times = [r["加工時間"] for r in scheduled]
            list_idx = proc_times.index(max(proc_times))
            t -= scheduled[list_idx]["加工時間"]
            rejected.append(scheduled[list_idx])
            scheduled.pop(list_idx)
    result = pd.DataFrame(scheduled + rejected)
    return result.reset_index(drop=True)


def compute_metrics(schedule_df):
    makespan = schedule_df["結束時間"].max()
    total_completion = schedule_df["結束時間"].sum()
    avg_completion = total_completion / len(schedule_df)
    late_jobs = schedule_df["是否延遲"].sum()
    total_lateness = schedule_df["延遲"].sum()
    max_lateness = schedule_df["延遲"].max()
    return {
        "Makespan": makespan,
        "平均完工時間": round(avg_completion, 2),
        "延遲工作數": late_jobs,
        "總延遲量": total_lateness,
        "最大延遲": max_lateness,
    }


def johnson_two_machine(jobs_df):
    """Johnson's algorithm for 2-machine flow shop."""
    jobs = jobs_df.copy().reset_index(drop=True)
    jobs["job_id"] = [f"J{i+1}" for i in range(len(jobs))]

    group1 = jobs[jobs["機器A"] <= jobs["機器B"]].sort_values("機器A")
    group2 = jobs[jobs["機器A"] > jobs["機器B"]].sort_values("機器B", ascending=False)
    ordered = pd.concat([group1, group2]).reset_index(drop=True)

    # Compute schedule for both machines
    schedule_a, schedule_b = [], []
    end_a = 0
    end_b = 0

    for _, row in ordered.iterrows():
        start_a = end_a
        end_a = start_a + row["機器A"]
        start_b = max(end_a, end_b)
        end_b = start_b + row["機器B"]
        schedule_a.append({
            "工作": row["job_id"],
            "機器": "機器 A",
            "開始時間": start_a,
            "結束時間": end_a,
            "加工時間": row["機器A"],
        })
        schedule_b.append({
            "工作": row["job_id"],
            "機器": "機器 B",
            "開始時間": start_b,
            "結束時間": end_b,
            "加工時間": row["機器B"],
        })

    return pd.DataFrame(schedule_a + schedule_b), ordered


def two_machine_custom_order(jobs_df, order):
    """Two-machine scheduling with custom job order."""
    schedule_a, schedule_b = [], []
    end_a = 0
    end_b = 0

    for jid in order:
        row = jobs_df[jobs_df["job_id"] == jid].iloc[0]
        start_a = end_a
        end_a = start_a + row["機器A"]
        start_b = max(end_a, end_b)
        end_b = start_b + row["機器B"]
        schedule_a.append({
            "工作": jid,
            "機器": "機器 A",
            "開始時間": start_a,
            "結束時間": end_a,
            "加工時間": row["機器A"],
        })
        schedule_b.append({
            "工作": jid,
            "機器": "機器 B",
            "開始時間": start_b,
            "結束時間": end_b,
            "加工時間": row["機器B"],
        })

    return pd.DataFrame(schedule_a + schedule_b)


# ════════════════════════════════════════════════════════════════════
#   GANTT CHART
# ════════════════════════════════════════════════════════════════════

COLORS = [
    "#1976d2", "#26a69a", "#7e57c2", "#ef5350",
    "#66bb6a", "#ffa726", "#ab47bc", "#29b6f6",
    "#ff7043", "#d4e157",
]

def make_single_gantt(schedule_df):
    fig = go.Figure()
    jobs = schedule_df["工作"].unique()
    color_map = {j: COLORS[i % len(COLORS)] for i, j in enumerate(jobs)}
    due_dates = dict(zip(schedule_df["工作"], schedule_df["到期時間"]))

    for _, row in schedule_df.iterrows():
        color = "#ef5350" if row["是否延遲"] else color_map[row["工作"]]
        late_text = f" ⚠️ 延遲 {row['延遲']}" if row["是否延遲"] else ""
        fig.add_trace(go.Bar(
            x=[row["加工時間"]],
            y=["機器"],
            base=[row["開始時間"]],
            orientation="h",
            marker=dict(
                color=color,
                line=dict(color="#0f1117", width=2),
                opacity=0.9,
            ),
            name=row["工作"],
            text=row["工作"],
            textposition="inside",
            textfont=dict(color="white", size=13, family="JetBrains Mono"),
            hovertemplate=(
                f"<b>{row['工作']}</b><br>"
                f"開始：{row['開始時間']}<br>"
                f"結束：{row['結束時間']}<br>"
                f"加工時間：{row['加工時間']}<br>"
                f"到期時間：{row['到期時間']}<br>"
                f"延遲：{row['延遲']}{late_text}<extra></extra>"
            ),
            showlegend=True,
        ))

    # Due date markers
    for job, due in due_dates.items():
        fig.add_vline(
            x=due,
            line=dict(color=color_map[job], width=1, dash="dot"),
            annotation_text=f"D({job})",
            annotation_position="top",
            annotation_font=dict(size=10, color=color_map[job]),
        )

    fig.update_layout(
        barmode="overlay",
        plot_bgcolor="#1a1f2e",
        paper_bgcolor="#0f1117",
        font=dict(color="#e8eaf0", family="Noto Sans TC"),
        height=200,
        margin=dict(l=10, r=20, t=30, b=40),
        xaxis=dict(
            title="時間",
            gridcolor="#2a3040",
            zeroline=False,
            tickfont=dict(family="JetBrains Mono", size=11),
        ),
        yaxis=dict(gridcolor="#2a3040", tickfont=dict(size=12)),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


def make_two_machine_gantt(schedule_df):
    fig = go.Figure()
    jobs = schedule_df["工作"].unique()
    color_map = {j: COLORS[i % len(COLORS)] for i, j in enumerate(jobs)}

    machines = ["機器 A", "機器 B"]
    for machine in machines:
        mdf = schedule_df[schedule_df["機器"] == machine]
        for _, row in mdf.iterrows():
            fig.add_trace(go.Bar(
                x=[row["加工時間"]],
                y=[machine],
                base=[row["開始時間"]],
                orientation="h",
                marker=dict(
                    color=color_map[row["工作"]],
                    line=dict(color="#0f1117", width=2),
                    opacity=0.88,
                ),
                name=row["工作"],
                text=row["工作"],
                textposition="inside",
                textfont=dict(color="white", size=12, family="JetBrains Mono"),
                hovertemplate=(
                    f"<b>{row['工作']} @ {machine}</b><br>"
                    f"開始：{row['開始時間']}<br>"
                    f"結束：{row['結束時間']}<br>"
                    f"加工時間：{row['加工時間']}<extra></extra>"
                ),
                showlegend=(machine == "機器 A"),
                legendgroup=row["工作"],
            ))

    fig.update_layout(
        barmode="overlay",
        plot_bgcolor="#1a1f2e",
        paper_bgcolor="#0f1117",
        font=dict(color="#e8eaf0", family="Noto Sans TC"),
        height=280,
        margin=dict(l=10, r=20, t=30, b=40),
        xaxis=dict(
            title="時間",
            gridcolor="#2a3040",
            zeroline=False,
            tickfont=dict(family="JetBrains Mono", size=11),
        ),
        yaxis=dict(
            gridcolor="#2a3040",
            tickfont=dict(size=13),
            categoryorder="array",
            categoryarray=["機器 B", "機器 A"],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


# ════════════════════════════════════════════════════════════════════
#   METRIC CARDS
# ════════════════════════════════════════════════════════════════════

def show_metrics(metrics: dict):
    cols = st.columns(len(metrics))
    icons = {"Makespan": "⏱", "平均完工時間": "📊", "延遲工作數": "⚠️", "總延遲量": "📉", "最大延遲": "🔴"}
    for col, (k, v) in zip(cols, metrics.items()):
        icon = icons.get(k, "")
        col.markdown(f"""
        <div class="metric-card">
            <div class="label">{icon} {k}</div>
            <div class="value">{v}</div>
            <div class="unit">{'件' if '數' in k else '時間單位'}</div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#   TAB 1 — 單機排程
# ════════════════════════════════════════════════════════════════════

tab1, tab2 = st.tabs(["🔧 單機排程", "⚙️ 雙機排程"])

with tab1:
    st.markdown('<div class="section-title">輸入設定</div>', unsafe_allow_html=True)

    col_cfg, col_algo = st.columns([1, 1])
    with col_cfg:
        n_jobs = st.number_input("工作數量", min_value=1, max_value=20, value=5, step=1, key="sm_n")
    with col_algo:
        algorithm = st.selectbox(
            "排程演算法",
            ["FCFS（先到先服務）", "SPT（最短加工時間）", "EDD（最早到期日）",
             "LPT（最長加工時間）", "最小化最大延遲（Moore）"],
            key="sm_algo",
        )

    # Algo info
    algo_info = {
        "FCFS（先到先服務）": "按照工作到達順序安排，無需排序。適用於公平性優先的情況。",
        "SPT（最短加工時間）": "優先處理加工時間最短的工作，可最小化平均完工時間與平均等待時間。",
        "EDD（最早到期日）": "優先處理到期日最早的工作，可最小化最大延遲量（Lmax）。",
        "LPT（最長加工時間）": "優先處理加工時間最長的工作，適用於某些平衡負載的情境。",
        "最小化最大延遲（Moore）": "Moore 演算法，最小化延遲工作的數量（# of tardy jobs）。",
    }
    st.markdown(f'<div class="info-box">💡 <b>{algorithm}</b>：{algo_info[algorithm]}</div>', unsafe_allow_html=True)

    # Job input table
    st.markdown('<div class="section-title">工作資料輸入</div>', unsafe_allow_html=True)

    if st.session_state.get("sm_n_prev") != n_jobs:
        st.session_state["sm_jobs_default"] = pd.DataFrame({
            "加工時間": [3, 5, 2, 8, 4][:n_jobs] + [3] * max(0, n_jobs - 5),
            "到期時間": [7, 10, 6, 15, 9][:n_jobs] + [10] * max(0, n_jobs - 5),
        })
        st.session_state["sm_n_prev"] = n_jobs

    edited = st.data_editor(
        st.session_state["sm_jobs_default"],
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "加工時間": st.column_config.NumberColumn("加工時間 (p)", min_value=1, max_value=999),
            "到期時間": st.column_config.NumberColumn("到期時間 (d)", min_value=1, max_value=999),
        },
        key="sm_editor",
    )

    st.markdown("---")

    if st.button("▶ 執行排程", key="sm_run", use_container_width=True, type="primary"):
        with st.spinner("計算中..."):
            schedule = schedule_single_machine(edited, algorithm)
            metrics = compute_metrics(schedule)

        st.markdown('<div class="section-title">效能指標</div>', unsafe_allow_html=True)
        show_metrics(metrics)

        st.markdown('<div class="section-title">甘特圖</div>', unsafe_allow_html=True)
        st.plotly_chart(make_single_gantt(schedule), use_container_width=True)

        st.markdown('<div class="section-title">排程明細</div>', unsafe_allow_html=True)

        display_df = schedule[["工作", "開始時間", "結束時間", "加工時間", "到期時間", "延遲", "是否延遲"]].copy()
        display_df["狀態"] = display_df["是否延遲"].map({True: "⚠️ 延遲", False: "✅ 準時"})
        display_df = display_df.drop(columns=["是否延遲"])

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "延遲": st.column_config.NumberColumn("延遲量"),
                "狀態": st.column_config.TextColumn("狀態"),
            },
        )

        # Compare all algorithms
        st.markdown('<div class="section-title">演算法比較</div>', unsafe_allow_html=True)
        all_algos = ["FCFS（先到先服務）", "SPT（最短加工時間）", "EDD（最早到期日）",
                     "LPT（最長加工時間）", "最小化最大延遲（Moore）"]
        comparison = []
        for algo in all_algos:
            s = schedule_single_machine(edited, algo)
            m = compute_metrics(s)
            comparison.append({"演算法": algo, **m})
        cdf = pd.DataFrame(comparison)
        st.dataframe(cdf, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════
#   TAB 2 — 雙機排程
# ════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown('<div class="section-title">輸入設定</div>', unsafe_allow_html=True)

    col_cfg2, col_mode = st.columns([1, 1])
    with col_cfg2:
        n_jobs2 = st.number_input("工作數量", min_value=1, max_value=12, value=4, step=1, key="dm_n")
    with col_mode:
        mode2 = st.selectbox(
            "排程模式",
            ["Johnson 最佳演算法", "自訂工序順序"],
            key="dm_mode",
        )

    mode_info = {
        "Johnson 最佳演算法": "Johnson's Algorithm：自動求解兩台機器 Flow Shop 排程的最小 Makespan 最佳解。規則：t(A) ≤ t(B) 者排前段（按 A 升冪），t(A) > t(B) 者排後段（按 B 降冪）。",
        "自訂工序順序": "手動拖曳或選擇工作的加工順序，系統計算對應 Makespan 並與 Johnson 最佳解比較。",
    }
    st.markdown(f'<div class="info-box">💡 {mode_info[mode2]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">工作資料輸入</div>', unsafe_allow_html=True)

    if st.session_state.get("dm_n_prev") != n_jobs2:
        st.session_state["dm_jobs_default"] = pd.DataFrame({
            "機器A": [5, 3, 8, 2][:n_jobs2] + [4] * max(0, n_jobs2 - 4),
            "機器B": [2, 6, 4, 5][:n_jobs2] + [3] * max(0, n_jobs2 - 4),
        })
        st.session_state["dm_n_prev"] = n_jobs2

    edited2 = st.data_editor(
        st.session_state["dm_jobs_default"],
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "機器A": st.column_config.NumberColumn("機器 A 加工時間", min_value=1, max_value=999),
            "機器B": st.column_config.NumberColumn("機器 B 加工時間", min_value=1, max_value=999),
        },
        key="dm_editor",
    )

    # Custom order selector
    custom_order = None
    if mode2 == "自訂工序順序":
        st.markdown('<div class="section-title">工序順序設定</div>', unsafe_allow_html=True)
        job_ids = [f"J{i+1}" for i in range(n_jobs2)]
        cols_order = st.columns(n_jobs2)
        order_selected = []
        available = job_ids.copy()
        for i, col in enumerate(cols_order):
            with col:
                choice = st.selectbox(
                    f"第 {i+1} 順位",
                    options=[j for j in available],
                    key=f"order_{i}",
                )
                order_selected.append(choice)
                if choice in available:
                    available = [j for j in available if j != choice]
        custom_order = order_selected

    st.markdown("---")

    if st.button("▶ 執行排程", key="dm_run", use_container_width=True, type="primary"):
        jobs_input = edited2.copy()
        jobs_input["job_id"] = [f"J{i+1}" for i in range(len(jobs_input))]

        with st.spinner("計算中..."):
            if mode2 == "Johnson 最佳演算法":
                schedule_df, ordered = johnson_two_machine(jobs_input)
                johnson_order = ordered["job_id"].tolist()
                makespan = schedule_df[schedule_df["機器"] == "機器 B"]["結束時間"].max()

                st.markdown('<div class="section-title">Johnson 最佳工序</div>', unsafe_allow_html=True)
                order_str = " → ".join(johnson_order)
                st.markdown(f"""
                <div class="info-box">
                    🏆 最佳排程順序：<b style="font-family:JetBrains Mono;color:#4fc3f7">{order_str}</b><br>
                    最小 Makespan = <b style="font-family:JetBrains Mono;color:#66bb6a">{makespan}</b>
                </div>
                """, unsafe_allow_html=True)
            else:
                schedule_df = two_machine_custom_order(jobs_input, custom_order)
                makespan = schedule_df[schedule_df["機器"] == "機器 B"]["結束時間"].max()

                # Compare with Johnson
                johnson_df, johnson_ordered = johnson_two_machine(jobs_input)
                johnson_makespan = johnson_df[johnson_df["機器"] == "機器 B"]["結束時間"].max()
                johnson_order = johnson_ordered["job_id"].tolist()
                gap = makespan - johnson_makespan
                gap_str = f"+{gap}" if gap > 0 else str(gap)
                color = "#ef5350" if gap > 0 else "#66bb6a"

                st.markdown('<div class="section-title">排程比較</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                c1.markdown(f"""
                <div class="metric-card">
                    <div class="label">📌 自訂順序 Makespan</div>
                    <div class="value" style="color:#ffa726">{makespan}</div>
                    <div class="unit">{'  →  '.join(custom_order)}</div>
                </div>
                """, unsafe_allow_html=True)
                c2.markdown(f"""
                <div class="metric-card">
                    <div class="label">🏆 Johnson 最佳 Makespan</div>
                    <div class="value" style="color:#66bb6a">{johnson_makespan}</div>
                    <div class="unit">{'  →  '.join(johnson_order)}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-box" style="margin-top:0.5rem">
                    與最佳解差距：<b style="color:{color};font-family:JetBrains Mono">{gap_str}</b> 時間單位
                    {'（已達最佳解 ✅）' if gap == 0 else '（尚未最佳化）'}
                </div>
                """, unsafe_allow_html=True)

        # Metrics
        idle_a = makespan - schedule_df[schedule_df["機器"] == "機器 A"]["加工時間"].sum()
        idle_b = makespan - schedule_df[schedule_df["機器"] == "機器 B"]["加工時間"].sum()
        util_a = round((1 - idle_a / makespan) * 100, 1)
        util_b = round((1 - idle_b / makespan) * 100, 1)

        st.markdown('<div class="section-title">效能指標</div>', unsafe_allow_html=True)
        m_cols = st.columns(4)
        for col, (label, val, unit) in zip(m_cols, [
            ("Makespan", makespan, "時間單位"),
            ("機器A 閒置", idle_a, "時間單位"),
            ("機器B 閒置", idle_b, "時間單位"),
            ("機器A 稼動率", f"{util_a}%", ""),
        ]):
            col.markdown(f"""
            <div class="metric-card">
                <div class="label">{label}</div>
                <div class="value">{val}</div>
                <div class="unit">{unit}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">甘特圖</div>', unsafe_allow_html=True)
        st.plotly_chart(make_two_machine_gantt(schedule_df), use_container_width=True)

        st.markdown('<div class="section-title">排程明細</div>', unsafe_allow_html=True)
        pivot = schedule_df.pivot(index="工作", columns="機器", values=["開始時間", "結束時間"])
        pivot.columns = [f"{m}_{t}" for t, m in pivot.columns]
        pivot = pivot.rename(columns={
            "機器 A_開始時間": "A 開始",
            "機器 A_結束時間": "A 結束",
            "機器 B_開始時間": "B 開始",
            "機器 B_結束時間": "B 結束",
        })
        pivot["等待時間(B-A)"] = pivot["B 開始"] - pivot["A 結束"]
        st.dataframe(pivot, use_container_width=True)