"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import vso_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def blocker_cells(stacks) -> set:
    """Container, die über einem früher abzurufenden im selben Stapel liegen (Position (Stapel, Lage))."""
    out = set()
    for i, s in enumerate(stacks):
        lowest = 10 ** 9
        for j, c in enumerate(s):
            if c > lowest:
                out.add((i, j))
            else:
                lowest = c
    return out


def build_bay(stacks, height, target=None):
    """Die Bucht als Säulen: je Lage ein Balken mit der Abrufnummer. Rot: blockiert einen früher abzurufenden, grün: nächster Abruf
    (`target`, eine Abrufnummer oder None), grau-blau: übrige."""
    blockers = blocker_cells(stacks)
    fig = go.Figure()
    xs = list(range(len(stacks)))
    for j in range(height):
        ys, colors, texts = [], [], []
        for i, s in enumerate(stacks):
            if j < len(s):
                c = s[j]
                ys.append(1)
                texts.append(str(c))
                colors.append(C.COLOR_TARGET if c == target else C.COLOR_BLOCK if (i, j) in blockers else C.COLOR_CELL)
            else:
                ys.append(0)
                texts.append("")
                colors.append(C.COLOR_CELL)
        fig.add_trace(go.Bar(x=xs, y=ys, base=j, marker_color=colors, text=texts, textposition="inside", insidetextanchor="middle",
                             textfont=dict(color="#ffffff", size=16), width=0.78, showlegend=False,
                             hovertemplate="Abruf %{text}<extra></extra>", marker_line=dict(width=0)))
    fig.update_layout(barmode="overlay")
    fig.add_hline(y=height, line_dash="dot", line_color="rgba(128,128,128,0.7)", annotation_text="Höchsthöhe", annotation_position="top left")
    fig.update_xaxes(tickvals=xs, ticktext=[f"Stapel {i + 1}" for i in xs], showgrid=False)
    fig.update_yaxes(range=[0, height + 0.35], showticklabels=False, showgrid=False, zeroline=False)
    return _base(fig, height=48 * height + 90)


def build_solvable(loesbar):
    """Anteil der lösbaren Buchten (Prozent) gegen die Zahl freier Plätze, je Zelle eine Linie. `loesbar`: {"s,h,f": pmp_stats}."""
    fig = go.Figure()
    for (s, h) in C.SOLVE_CELLS:
        fs = list(range(1, C.SOLVE_FREE_MAX + 1))
        fig.add_trace(go.Scatter(x=fs, y=[100.0 * loesbar[f"{s},{h},{f}"]["solved"] / loesbar[f"{s},{h},{f}"]["n"] for f in fs], mode="lines+markers", name=f"{s} Stapel, Höhe {h}",
                                 line=dict(color=C.COLOR_LINES[h], dash="solid" if s == 4 else "dot" if h == 3 else "dash"), hovertemplate="%{x} frei: %{y:.0f} %<extra>%{fullData.name}</extra>"))
    fig.update_xaxes(title_text="freie Plätze", tickvals=list(range(1, C.SOLVE_FREE_MAX + 1)))
    fig.update_yaxes(title_text="lösbare Buchten (%)", range=[0, 105])
    return _base(fig, height=340)


def build_ratio(loesbar):
    """Optimum / Untergrenze (Mittel über die gelösten Buchten) gegen die Zahl freier Plätze, je Zelle eine Linie; nur Zeilen mit mindestens einer gelösten Bucht. `loesbar`: {"s,h,f": pmp_stats}."""
    fig = go.Figure()
    for (s, h) in C.SOLVE_CELLS:
        fs = [f for f in range(1, C.SOLVE_FREE_MAX + 1) if loesbar[f"{s},{h},{f}"]["ratio"] is not None and loesbar[f"{s},{h},{f}"]["solved"] >= 10]
        fig.add_trace(go.Scatter(x=fs, y=[loesbar[f"{s},{h},{f}"]["ratio"] for f in fs], mode="lines+markers", name=f"{s} Stapel, Höhe {h}",
                                 line=dict(color=C.COLOR_LINES[h], dash="solid" if s == 4 else "dot" if h == 3 else "dash"), hovertemplate="%{x} frei: %{y:.2f}<extra>%{fullData.name}</extra>"))
    fig.update_xaxes(title_text="freie Plätze (Zeilen mit mindestens 10 gelösten Buchten)", tickvals=list(range(1, C.SOLVE_FREE_MAX + 1)))
    fig.update_yaxes(title_text="Optimum / Untergrenze", rangemode="tozero")
    return _base(fig, height=340)


def build_vs(vs):
    """Mittleres Optimum des Pre-Marshalling und des Relocation beim Abruf je Zelle und freien Plätzen; dazu die Untergrenze. `vs`: {"s,h,f": vs_stats}."""
    keys = sorted(vs, key=lambda k: tuple(int(x) for x in k.split(",")))
    x = [f"{k.split(',')[0]} × {k.split(',')[1]}, {k.split(',')[2]} frei" for k in keys]
    fig = go.Figure()
    for name, field, color in (("Pre-Marshalling", "p", C.COLOR_PMP), ("Relocation beim Abruf", "r", C.COLOR_RELOC), ("Untergrenze (Blocker)", "lb1", C.COLOR_LB)):
        fig.add_trace(go.Bar(x=x, y=[vs[k][field] for k in keys], name=name, marker_color=color, hovertemplate="%{x}: %{y:.2f}<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category", title_text="Zelle (Stapel × Höhe), freie Plätze")
    fig.update_yaxes(title_text="Hübe (Mittel)", rangemode="tozero")
    return _base(fig, height=360)
