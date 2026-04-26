"""
Intelligence Pro — ui/components.py
Componentes HTML reutilizables en todas las páginas.
"""
import streamlit as st
import hashlib
from typing import Optional


# ─── Helpers ────────────────────────────────────────────────

def safe_key(*parts) -> str:
    """Genera key MD5 única para widgets en loops."""
    raw = "_".join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def signal_class(ev: float, prob: float, edge: float) -> str:
    """Retorna clase CSS según semáforo de valor."""
    if ev > 0 and prob >= 0.40 and edge >= 0.03:
        return "green"
    elif ev > 0:
        return "amber"
    elif ev > -0.05:
        return "orange"
    return "red"


def signal_emoji(cls: str) -> str:
    return {"green": "🟢", "amber": "🟡", "orange": "🟠", "red": "🔴"}.get(cls, "⚪")


def fmt_momio_americano(decimal: float) -> str:
    """Convierte momio decimal a americano para referencia."""
    if decimal >= 2.0:
        return f"+{int((decimal - 1) * 100)}"
    elif decimal > 1.0:
        return f"-{int(100 / (decimal - 1))}"
    return "N/A"


# ─── Bankroll widget (sidebar) ───────────────────────────────

def bankroll_sidebar():
    """Widget de bankroll para el sidebar. Mostrar al inicio de cada página."""
    ss = st.session_state
    bankroll = ss.get("bankroll", 1000.0)
    bankroll_inicial = ss.get("bankroll_inicial", 1000.0)
    historial = ss.get("historial", [])
    jornada = ss.get("jornada_activa", [])

    delta = bankroll - bankroll_inicial
    pct = (delta / bankroll_inicial * 100) if bankroll_inicial else 0
    delta_str = f"{'↑' if delta >= 0 else '↓'} ${abs(delta):,.0f} ({abs(pct):.1f}%)"
    picks_str = f"{len(jornada)} pick{'s' if len(jornada) != 1 else ''} esta jornada"

    st.markdown((f"""
    <div class="bankroll-widget">
        <div class="bankroll-label">Bankroll</div>
        <div class="bankroll-amount">${bankroll:,.0f} <span style="font-size:1rem;font-weight:400;opacity:.6">MXN</span></div>
        <div class="bankroll-delta">{delta_str}</div>
        <div class="bankroll-picks">{picks_str}</div>
    </div>
    """).strip(), unsafe_allow_html=True)


# ─── Pipeline stepper ────────────────────────────────────────

def pipeline_steps():
    """
    Muestra los 4 pasos del flujo semanal con estado visual.
    done / active / pending basado en session_state.
    """
    ss = st.session_state
    fbref_data = ss.get("fbref_data", {})
    fixtures_data = ss.get("fixtures_data", {})
    momios_data = ss.get("momios_data", {})
    jornada = ss.get("jornada_activa", [])
    historial = ss.get("historial", [])

    ligas_con_datos = sum(1 for v in fbref_data.values() if v)
    ligas_con_fixtures = sum(1 for v in fixtures_data.values() if v)
    partidos_con_momios = sum(
        1 for partidos in momios_data.values()
        for p in partidos.values() if p
    ) if isinstance(momios_data, dict) else 0

    step1_done = ligas_con_datos >= 1 and ligas_con_fixtures >= 1
    step2_done = partidos_con_momios >= 1
    step3_done = len(jornada) >= 1
    step4_done = any(b.get("resultado") is not None for b in historial)

    def step_html(num, label, sub, status):
        cls = {"done": "done", "active": "active", "pending": "pending"}.get(status, "pending")
        icon = "✓" if status == "done" else str(num)
        return f"""
        <div class="ip-step {cls}">
            <div class="ip-step-num">{icon}</div>
            <div class="ip-step-info">
                <div class="ip-step-label">{label}</div>
                <div class="ip-step-sub">{sub}</div>
            </div>
        </div>"""

    def status(done, prev_done):
        if done:
            return "done"
        if prev_done:
            return "active"
        return "pending"

    s1 = "done" if step1_done else "active"
    s2 = status(step2_done, step1_done)
    s3 = status(step3_done, step2_done)
    s4 = status(step4_done, step3_done)

    sub1 = f"{ligas_con_datos} liga{'s' if ligas_con_datos != 1 else ''}" if step1_done else "sin datos"
    sub2 = f"{partidos_con_momios} partidos" if step2_done else "pendiente"
    sub3 = f"{len(jornada)} picks" if step3_done else "pendiente"
    sub4 = "registrado" if step4_done else "pendiente"

    html = f"""
    <div class="ip-pipeline">
        {step_html(1, 'Cargar Ligas', sub1, s1)}
        {step_html(2, 'Momios', sub2, s2)}
        {step_html(3, 'Picks', sub3, s3)}
        {step_html(4, 'Resultados', sub4, s4)}
    </div>"""
    st.markdown((html).strip(), unsafe_allow_html=True)


# ─── Next action CTA ──────────────────────────────────────────

def next_action_cta():
    """Muestra la acción recomendada según el estado actual."""
    ss = st.session_state
    fbref_data = ss.get("fbref_data", {})
    momios_data = ss.get("momios_data", {})
    jornada = ss.get("jornada_activa", [])

    ligas_cargadas = sum(1 for v in fbref_data.values() if v)
    partidos_con_momios = sum(
        1 for partidos in momios_data.values()
        for p in partidos.values() if p
    ) if isinstance(momios_data, dict) else 0

    if ligas_cargadas == 0:
        icon, title, sub = "📋", "Carga tus ligas para empezar", "Ve a Datos → pega las tablas de FBRef de la semana"
    elif partidos_con_momios == 0:
        icon, title, sub = "💰", "Agrega los momios de esta jornada", "Ve a Momios → pega el JSON de Team Mexico o edita directo"
    elif len(jornada) == 0:
        icon, title, sub = "🎯", "Elige tus picks de la semana", "Ve a Análisis → filtra los 🟢 y agrega los mejores"
    else:
        icon, title, sub = "✅", f"Tienes {len(jornada)} picks listos", "Registra los resultados al final de la jornada"

    st.markdown((f"""
    <div class="next-action">
        <div class="next-action-icon">{icon}</div>
        <div class="next-action-text">
            <div class="next-action-title">{title}</div>
            <div class="next-action-sub">{sub}</div>
        </div>
    </div>
    """).strip(), unsafe_allow_html=True)


# ─── Liga status card ──────────────────────────────────────────

TABLA_NOMBRES = {
    "standard":   "Estándar",
    "shooting":   "Disparos",
    "passing":    "Pases",
    "passtypes":  "Tipo Pase",
    "gca":        "GCA/SCA",
    "defense":    "Defensa",
    "possession": "Posesión",
    "playingtime":"Minutos",
    "misc":       "Misc",
    "ha":         "Casa/Vis",
}

def liga_status_card(liga_key: str, liga_display: str, tablas_cargadas: dict):
    """Tarjeta de estado de carga de una liga."""
    total = len(TABLA_NOMBRES)
    cargadas = sum(1 for v in tablas_cargadas.values() if v is not None)
    pct = int(cargadas / total * 100)

    badges = ""
    for key, nombre in TABLA_NOMBRES.items():
        ok = tablas_cargadas.get(key) is not None
        cls = "ok" if ok else "miss"
        badges += f'<span class="table-badge {cls}">{nombre}</span>'

    st.markdown((f"""
    <div class="liga-status-card">
        <div class="liga-status-header">
            <div class="liga-name">{liga_display}</div>
            <div class="liga-pct">{cargadas}/{total}</div>
        </div>
        <div class="tables-grid">{badges}</div>
        <div class="table-progress-bar">
            <div class="table-progress-fill" style="width:{pct}%"></div>
        </div>
    </div>
    """).strip(), unsafe_allow_html=True)


# ─── Match card (Análisis) ──────────────────────────────────────

def match_card_header(home: str, away: str, liga: str, fecha: str, sig_class: str):
    """Header de tarjeta de partido."""
    st.markdown(f"""
    <div class="match-card {sig_class}">
        <div class="match-meta">{liga} · {fecha}</div>
        <div class="match-teams">{home} <span style="color:var(--text-muted);font-weight:400">vs</span> {away}</div>
    </div>
    """, unsafe_allow_html=True)


def market_chips(mercados: list[dict]):
    """
    Renderiza chips de mercado con señal, momio y EV.
    mercados: [{"nombre": "1X2 Local", "momio": 1.85, "ev": 0.08, "prob": 0.52, "signal": "green"}]
    """
    chips_html = '<div class="match-market-row">'
    for m in mercados[:3]:  # máximo 3 chips visibles
        cls = m.get("signal", "amber")
        ev_str = f"EV {m['ev']*100:+.1f}%" if "ev" in m else ""
        prob_str = f"{m.get('prob', 0)*100:.0f}%"
        chips_html += f"""
        <span class="market-chip {cls}">
            {signal_emoji(cls)} {m['nombre']}
        </span>
        <span class="market-odds">{m.get('momio', '')}</span>
        <span class="market-ev">{ev_str} · {prob_str}</span>
        """
    chips_html += '</div>'
    st.markdown((chips_html).strip(), unsafe_allow_html=True)


# ─── Fuzzy match confirmation ────────────────────────────────────

def fuzzy_confirm_block(pending_matches: list[dict]) -> dict:
    """
    Muestra los matches de fuzzy que necesitan confirmación.
    pending_matches: [{"json_name": "Man Utd", "fbref_name": "Manchester United", "score": 0.82}]
    Returns: dict de confirmaciones {json_name: confirmed_fbref_name}
    """
    if not pending_matches:
        return {}

    st.markdown(f"""
    <div class="section-header">
        <div class="section-title">⚠️ Confirmar nombres de equipos</div>
        <div class="section-count">{len(pending_matches)} pendientes</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(("""
    <div class="inline-tip">
        El sistema encontró <strong>posibles coincidencias</strong> pero no está seguro.
        Confirma o corrige cada una antes de cargar los momios.
    </div>
    """).strip(), unsafe_allow_html=True)

    confirmed = {}
    for i, match in enumerate(pending_matches):
        col1, col2, col3 = st.columns([3, 3, 2])
        with col1:
            st.markdown((f"""
            <div class="fuzzy-card">
                <div class="fuzzy-title">📋 En el JSON</div>
                <div class="fuzzy-match">{match['json_name']}</div>
            </div>
            """).strip(), unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="fuzzy-card" style="background:var(--s-green-bg);border-color:var(--s-green-border)">
                <div class="fuzzy-title" style="color:var(--s-green)">✓ Mejor coincidencia</div>
                <div class="fuzzy-match">{match['fbref_name']} ({match.get('score', 0)*100:.0f}%)</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            key = safe_key("fuzzy_confirm", i, match['json_name'])
            # Opciones: confirmar la sugerencia o corregir manualmente
            opciones = [match['fbref_name']] + match.get('alternativas', []) + ["✏️ Otro..."]
            sel = st.selectbox("Confirmar", opciones, key=key, label_visibility="collapsed")
            if sel == "✏️ Otro...":
                key2 = safe_key("fuzzy_manual", i, match['json_name'])
                sel = st.text_input("Nombre exacto", key=key2, placeholder="Escribir nombre...")
        if sel and sel != "✏️ Otro...":
            confirmed[match['json_name']] = sel

    return confirmed


# ─── Inline momios editor ──────────────────────────────────────

def momios_inline_editor(partidos: list[dict]) -> dict:
    """
    Editor inline de momios. Muestra tabla editable con inputs por partido.
    Returns: {partido_key: {"home": float, "draw": float, "away": float}}
    """
    if not partidos:
        st.info("No hay partidos cargados. Ve a Datos primero.")
        return {}

    st.markdown(("""
    <div class="inline-tip">
        <strong>Formato americano:</strong> -110, +150, +200 · 
        <strong>Decimal:</strong> 1.90, 2.50, 3.00 · 
        Deja en blanco si no quieres apostar ese partido.
    </div>
    """).strip(), unsafe_allow_html=True)

    momios_editados = {}

    # Header visual
    hdr_cols = st.columns([4, 2, 2, 2])
    hdr_cols[0].markdown("**Partido**")
    hdr_cols[1].markdown("**Local**")
    hdr_cols[2].markdown("**Empate**")
    hdr_cols[3].markdown("**Visitante**")

    st.markdown(("<hr style='margin:6px 0'>").strip(), unsafe_allow_html=True)

    for i, p in enumerate(partidos):
        key_prefix = safe_key("momio_inline", i, p.get("home", ""), p.get("away", ""))
        cols = st.columns([4, 2, 2, 2])

        with cols[0]:
            st.markdown(
                f"<div style='font-family:var(--font-ui);font-weight:600;font-size:0.85rem;"
                f"color:var(--text);padding:6px 0'>{p.get('home','?')} vs {p.get('away','?')}"
                f"<br><span style='font-size:0.7rem;color:var(--text-muted)'>"
                f"{p.get('liga','')} · {p.get('fecha','')}</span></div>",
                unsafe_allow_html=True
            )

        existing = p.get("momios", {})
        with cols[1]:
            h_val = existing.get("home", "")
            h_input = st.text_input(
                "Local", value=str(h_val) if h_val else "",
                placeholder="-110", key=f"h_{key_prefix}",
                label_visibility="collapsed"
            )
        with cols[2]:
            d_val = existing.get("draw", "")
            d_input = st.text_input(
                "Empate", value=str(d_val) if d_val else "",
                placeholder="+280", key=f"d_{key_prefix}",
                label_visibility="collapsed"
            )
        with cols[3]:
            a_val = existing.get("away", "")
            a_input = st.text_input(
                "Visitante", value=str(a_val) if a_val else "",
                placeholder="+200", key=f"a_{key_prefix}",
                label_visibility="collapsed"
            )

        partido_key = f"{p.get('home','')}_{p.get('away','')}_{p.get('fecha','')}"
        momios_editados[partido_key] = {
            "home": h_input, "draw": d_input, "away": a_input,
            "meta": p
        }

    return momios_editados


# ─── Sección header ────────────────────────────────────────────

def section_header(title: str, count: Optional[int] = None):
    count_html = f'<div class="section-count">{count}</div>' if count is not None else ""
    st.markdown((f"""
    <div class="section-header">
        <div class="section-title">{title}</div>
        {count_html}
    </div>
    """).strip(), unsafe_allow_html=True)


# ─── Toast ────────────────────────────────────────────────────

def toast(msg: str, tipo: str = "success"):
    """Tipo: success | error | info"""
    st.markdown((f'<div class="ip-toast {tipo}">{msg}</div>').strip(), unsafe_allow_html=True)


# ─── Inline tip ───────────────────────────────────────────────

def inline_tip(html: str):
    st.markdown((f'<div class="inline-tip">{html}</div>').strip(), unsafe_allow_html=True)


# ─── Auto-save indicator ───────────────────────────────────────

def auto_save_indicator():
    """Muestra estado de la sesión + botón de guardar en sidebar."""
    ss = st.session_state
    modificada = ss.get("_session_modified", False)

    if modificada:
        st.sidebar.markdown("""
        <div class="ip-toast info" style="margin:0 0 10px">
            💾 Sesión sin guardar
        </div>
        """, unsafe_allow_html=True)

    if st.sidebar.button("⬇ Exportar sesión", use_container_width=True):
        from data.session import export_session
        json_str = export_session()
        st.sidebar.download_button(
            "📥 Descargar JSON",
            data=json_str,
            file_name="intelligence_pro_session.json",
            mime="application/json",
            use_container_width=True
        )
        ss["_session_modified"] = False

    # Cargar sesión
    with st.sidebar.expander("📤 Cargar sesión"):
        uploaded = st.file_uploader(
            "Sube el JSON guardado",
            type=["json"],
            key="session_upload",
            label_visibility="collapsed"
        )
        if uploaded:
            from data.session import import_session
            try:
                import_session(uploaded.read().decode("utf-8"))
                toast("✅ Sesión cargada correctamente", "success")
                ss["_session_modified"] = False
                st.rerun()
            except Exception as e:
                toast(f"❌ Error al cargar: {e}", "error")


# ─── Marcar sesión como modificada ────────────────────────────

def mark_modified():
    st.session_state["_session_modified"] = True
