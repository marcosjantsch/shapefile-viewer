from __future__ import annotations

import streamlit as st


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --seg-bg: #f1f7ff;
            --seg-bg-soft: #edf7ff;
            --seg-surface: rgba(255, 255, 255, 0.86);
            --seg-card: #ffffff;
            --seg-card-2: #f8fcff;
            --seg-line: rgba(19, 78, 124, 0.14);
            --seg-line-strong: rgba(19, 78, 124, 0.24);
            --seg-ink: #163653;
            --seg-muted: #617d97;
            --seg-accent: #156ea8;
            --seg-accent-2: #8fd12a;
            --seg-accent-3: #c18d46;
            --seg-accent-4: #2ca8c9;
            --seg-success: #5aa114;
            --seg-warning: #b7772f;
            --seg-danger: #c5483b;
            --seg-shadow: 0 18px 40px rgba(22, 54, 83, 0.11);
        }

        html, body, [class*="css"], [data-testid="stAppViewContainer"], .stApp {
            font-family: 'Manrope', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(21, 110, 168, 0.18), transparent 25%),
                radial-gradient(circle at top right, rgba(143, 209, 42, 0.18), transparent 19%),
                radial-gradient(circle at 50% 0%, rgba(193, 141, 70, 0.10), transparent 20%),
                linear-gradient(180deg, #f7fbff 0%, #eef6ff 42%, #f7fbff 100%);
            color: var(--seg-ink);
        }

        [data-testid="stHeader"] {
            background: rgba(0, 0, 0, 0);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(239,248,255,0.99));
            border-right: 1px solid var(--seg-line);
            box-shadow: inset -1px 0 0 rgba(255,255,255,0.65);
        }

        [data-testid="stSidebar"] * {
            color: var(--seg-ink) !important;
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 2.2rem;
        }

        .seg-header {
            position: sticky;
            top: 0.1rem;
            z-index: 30;
            margin-bottom: 1rem;
        }

        .seg-header-card {
            border: 1px solid rgba(255, 255, 255, 0.78);
            border-radius: 24px;
            padding: 1rem 1.1rem;
            background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(244,250,255,0.94));
            box-shadow: var(--seg-shadow);
            backdrop-filter: blur(12px);
        }

        .seg-header-title {
            font-size: 1.5rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: var(--seg-ink);
            margin: 0;
        }

        .seg-header-subtitle {
            margin-top: 0.24rem;
            color: var(--seg-muted);
            font-size: 0.95rem;
        }

        .seg-header-session {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            justify-content: flex-end;
            align-items: center;
        }

        .seg-page-intro {
            margin-bottom: 1rem;
        }

        .seg-page-intro h1 {
            font-size: 1.6rem;
            margin: 0.2rem 0 0.35rem 0;
            color: var(--seg-ink);
            letter-spacing: -0.03em;
        }

        .seg-page-intro p {
            margin: 0;
            color: var(--seg-muted);
            max-width: 64rem;
            font-size: 0.96rem;
        }

        .seg-page-kicker {
            display: inline-flex;
            align-items: center;
            padding: 0.34rem 0.75rem;
            border-radius: 999px;
            border: 1px solid rgba(21, 110, 168, 0.14);
            background: linear-gradient(135deg, rgba(21,110,168,0.16), rgba(143,209,42,0.12));
            color: var(--seg-accent);
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .seg-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.28rem 0.68rem;
            border-radius: 999px;
            border: 1px solid transparent;
            background: rgba(21, 110, 168, 0.10);
            font-size: 0.77rem;
            font-weight: 700;
            white-space: nowrap;
        }

        .seg-badge--success {
            color: var(--seg-success);
            border-color: rgba(90, 161, 20, 0.18);
            background: rgba(90, 161, 20, 0.10);
        }

        .seg-badge--warning {
            color: var(--seg-warning);
            border-color: rgba(183, 119, 47, 0.18);
            background: rgba(183, 119, 47, 0.10);
        }

        .seg-badge--danger {
            color: var(--seg-danger);
            border-color: rgba(197, 72, 59, 0.15);
            background: rgba(197, 72, 59, 0.08);
        }

        .seg-badge--muted {
            color: var(--seg-muted);
            border-color: rgba(97, 125, 151, 0.10);
            background: rgba(97, 125, 151, 0.08);
        }

        .seg-metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.95rem;
            margin: 0.95rem 0 1.15rem 0;
        }

        .seg-metric-card {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.76);
            border-radius: 20px;
            padding: 1rem 1rem 1.05rem 1rem;
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(246,251,255,0.96));
            box-shadow: var(--seg-shadow);
        }

        .seg-metric-card::before {
            content: "";
            position: absolute;
            inset: 0 auto auto 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, var(--seg-accent), var(--seg-accent-4), var(--seg-accent-2), var(--seg-accent-3));
        }

        .seg-metric-card::after {
            content: "";
            position: absolute;
            right: -22px;
            top: -22px;
            width: 84px;
            height: 84px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(143,209,42,0.18), transparent 68%);
        }

        .seg-metric-card strong {
            display: block;
            font-size: 1.62rem;
            margin: 0.25rem 0;
            color: var(--seg-ink);
        }

        .seg-metric-card span {
            display: block;
            color: var(--seg-muted);
            font-size: 0.89rem;
            line-height: 1.4;
        }

        .seg-metric-card small {
            color: var(--seg-accent);
            font-size: 0.79rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .seg-record-card {
            border: 1px solid rgba(255,255,255,0.84);
            border-radius: 20px;
            padding: 1rem 1.05rem;
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(247,251,255,0.95));
            box-shadow: var(--seg-shadow);
            margin-bottom: 0.85rem;
        }

        .seg-record-title {
            font-size: 1.03rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
            color: var(--seg-ink);
        }

        .seg-record-meta {
            color: var(--seg-muted);
            font-size: 0.89rem;
            line-height: 1.48;
        }

        .seg-record-actions {
            margin-top: 0.8rem;
        }

        .seg-empty-state {
            display: flex;
            flex-direction: column;
            gap: 0.42rem;
            padding: 1rem;
            border: 1px dashed rgba(21, 110, 168, 0.24);
            border-radius: 18px;
            color: var(--seg-muted);
            background: rgba(255, 255, 255, 0.74);
        }

        .seg-login-wrap {
            max-width: 1040px;
            margin: 0 auto;
            padding-top: 1rem;
        }

        .seg-login-hero {
            border: 1px solid rgba(255,255,255,0.84);
            border-radius: 28px;
            padding: 1.25rem;
            background: linear-gradient(135deg, rgba(255,255,255,0.97), rgba(239,248,255,0.95));
            box-shadow: var(--seg-shadow);
            margin-bottom: 1rem;
        }

        .seg-login-hero h1 {
            margin: 0 0 0.45rem 0;
            color: var(--seg-ink);
            letter-spacing: -0.03em;
        }

        .seg-login-hero p {
            margin: 0;
            color: var(--seg-muted);
            font-size: 0.96rem;
        }

        .seg-demo-banner {
            border: 1px solid rgba(184, 135, 69, 0.22);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            background: linear-gradient(135deg, rgba(184,135,69,0.12), rgba(255,255,255,0.86));
            color: #8a5d24;
            margin-bottom: 1rem;
            box-shadow: 0 10px 24px rgba(184, 135, 69, 0.10);
        }

        .seg-sidebar-brand {
            padding: 0.15rem 0 1rem 0;
        }

        .seg-sidebar-brand strong {
            display: block;
            font-size: 1.12rem;
            color: var(--seg-ink);
        }

        .seg-sidebar-brand span {
            color: var(--seg-muted);
            font-size: 0.86rem;
        }

        .stButton > button,
        .stForm button[kind="secondaryFormSubmit"],
        .stDownloadButton > button {
            border-radius: 14px;
            border: 1px solid rgba(21, 110, 168, 0.14);
            background: linear-gradient(180deg, #ffffff, #eef8ff);
            color: var(--seg-ink);
            font-weight: 700;
            box-shadow: 0 8px 18px rgba(41, 72, 123, 0.07);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: rgba(21, 110, 168, 0.24);
            box-shadow: 0 12px 24px rgba(21, 110, 168, 0.10);
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, rgba(21,110,168,0.96), rgba(44,168,201,0.94), rgba(143,209,42,0.90));
            color: #ffffff;
            border-color: rgba(21, 110, 168, 0.24);
        }

        div[data-testid="stForm"] {
            border: 1px solid rgba(255,255,255,0.84);
            border-radius: 20px;
            background: linear-gradient(180deg, rgba(255,255,255,0.97), rgba(248,251,255,0.94));
            box-shadow: var(--seg-shadow);
            padding: 0.95rem 0.95rem 0.2rem 0.95rem;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(255,255,255,0.84);
            border-radius: 20px;
            overflow: hidden;
            background: rgba(255,255,255,0.96);
            box-shadow: var(--seg-shadow);
        }

        label, .stSelectbox label, .stDateInput label, .stTextInput label, .stTextArea label {
            color: var(--seg-ink) !important;
        }

        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea {
            color: var(--seg-ink) !important;
        }

        .seg-video-frame {
            border: 1px solid rgba(255,255,255,0.82);
            border-radius: 20px;
            padding: 1rem;
            background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(239,248,255,0.95));
            box-shadow: var(--seg-shadow);
        }

        div[data-testid="stVideo"] {
            max-width: min(100%, 560px);
            margin: 0.75rem auto 0.35rem auto;
        }

        div[data-testid="stVideo"] video {
            width: 100% !important;
            max-height: 315px;
            aspect-ratio: 16 / 9;
            border-radius: 18px;
            background: #06131f;
            object-fit: contain;
        }

        .stAlert {
            border-radius: 18px;
        }

        @media (max-width: 980px) {
            .seg-metric-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .seg-header-session {
                justify-content: flex-start;
            }
        }

        @media (max-width: 640px) {
            .block-container {
                padding-top: 0.8rem;
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }

            .seg-metric-grid {
                grid-template-columns: 1fr;
            }

            .seg-page-intro h1 {
                font-size: 1.34rem;
            }

            div[data-testid="stVideo"] {
                max-width: 100%;
                margin-top: 0.55rem;
            }

            div[data-testid="stVideo"] video {
                max-height: 38vh;
                border-radius: 14px;
            }

            .seg-header-card,
            .seg-login-hero,
            .seg-record-card,
            .seg-metric-card,
            div[data-testid="stForm"],
            div[data-testid="stDataFrame"] {
                border-radius: 18px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
