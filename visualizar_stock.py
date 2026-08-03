"""
Dashboard HTML interactivo a partir del CSV que tira meli_vehiculos_scraper.py
=================================================================================
Uso:
    python visualizar_stock.py stock.csv --salida dashboard.html

Requisitos:
    pip install pandas plotly

Después de correrlo, abrí el .html generado con doble clic (se abre en el navegador,
no hace falta internet ni instalar nada más). Los gráficos son interactivos: podés
zoomear, sacar/poner marcas del gráfico clickeando en la leyenda, y pasar el mouse
sobre un punto para ver el detalle del auto.
"""

import argparse
import json
from pathlib import Path
import re

import pandas as pd


def limpiar_numero(valor):
    """Convierte '22.600.000' o '44.500' (formato AR) a un int de Python."""
    if pd.isna(valor):
        return None
    solo_digitos = re.sub(r"[^\d]", "", str(valor))
    return int(solo_digitos) if solo_digitos else None


def cargar(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        dtype={
            "kms": "string",
            "precio": "string",
            "anio": "string",
        },
        keep_default_na=False,
    )
    df["precio_num"] = df["precio"].apply(limpiar_numero)
    df["kms_num"] = df["kms"].apply(limpiar_numero)
    df["anio_num"] = pd.to_numeric(df["anio"], errors="coerce")
    return df


def armar_dashboard(df: pd.DataFrame, salida: str):
    tabla = df[["titulo", "marca", "modelo", "version", "anio", "kms", "precio", "link", "precio_num", "kms_num", "anio_num"]].copy()
    tabla = tabla.fillna("")

    marcas = sorted([m for m in tabla["marca"].dropna().unique() if str(m).strip()])
    modelos = sorted([m for m in tabla["modelo"].dropna().unique() if str(m).strip()])
    anios = sorted(
        [int(a) for a in pd.to_numeric(tabla["anio_num"], errors="coerce").dropna().unique()],
        reverse=True,
    )
    total_marcas = len(marcas)
    total_modelos = len(modelos)

    anios_validos = pd.to_numeric(df["anio_num"], errors="coerce").dropna()
    kms_validos = pd.to_numeric(df["kms_num"], errors="coerce").dropna()

    datos_json = tabla.to_dict(orient="records")
    salida_path = Path(salida)
    data_filename = f"{salida_path.stem}_data.json"
    data_path = salida_path.with_name(data_filename)

    with open(data_path, "w", encoding="utf-8") as data_file:
        json.dump(datos_json, data_file, ensure_ascii=False)

    with open(salida, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'><title>Dashboard de stock</title>")
        f.write("<link rel='preconnect' href='https://fonts.googleapis.com'>")
        f.write("<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>")
        f.write("<link href='https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap' rel='stylesheet'>")
        f.write("<script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script>")
        f.write(
            "<style>"
            ":root{--bg:#eef2f7;--bg2:#f7f9fc;--card:#ffffff;--card2:#f9fbff;--ink:#0f172a;--muted:#64748b;--accent:#2563eb;--accent2:#06b6d4;--line:#d9e2ef;--shadow:0 18px 50px rgba(15,23,42,.08)}"
            "*{box-sizing:border-box}"
            "body{margin:0;padding:28px;background:radial-gradient(circle at top left,#dbeafe 0,#eef2f7 34%,#f8fafc 100%);font-family:'Outfit','Segoe UI',Tahoma,sans-serif;color:var(--ink);position:relative;overflow-x:hidden}"
            "body:before,body:after{content:'';position:fixed;border-radius:999px;pointer-events:none;z-index:0;filter:blur(2px)}"
            "body:before{width:460px;height:460px;left:-160px;top:-140px;background:radial-gradient(circle,#93c5fd66,#0000 68%)}"
            "body:after{width:520px;height:520px;right:-220px;bottom:-220px;background:radial-gradient(circle,#22d3ee33,#0000 68%)}"
            ".shell{position:relative;z-index:1;max-width:1440px;margin:0 auto;display:block}"
            ".content{display:block}"
            "h1{margin:0;font-size:38px;line-height:1.05;letter-spacing:-.04em;font-weight:700;color:#081120}"
            "p.sub{margin:8px 0 0 0;color:var(--muted);font-size:14px}"
            ".top-band{display:grid;grid-template-columns:1.55fr 1fr;gap:16px;align-items:stretch;margin:18px 0 18px 0}"
            ".hero{display:grid;grid-template-columns:1.15fr 1fr 1fr;gap:12px;margin:0;align-items:stretch}"
            ".hero-card,.mini,.panel,.kpi,table{backdrop-filter:blur(10px)}"
            ".hero-card{border-radius:24px;padding:22px;border:1px solid #d7e3f3;background:linear-gradient(135deg,#ffffff 0,#eff6ff 100%);box-shadow:var(--shadow);position:relative;overflow:hidden}"
            ".hero-card:after{content:'';position:absolute;inset:auto -60px -70px auto;width:180px;height:180px;border-radius:50%;background:radial-gradient(circle,#38bdf822,#0000 70%)}"
            ".hero-card h3{margin:0;font-size:12px;color:#3b82f6;font-weight:700;letter-spacing:.12em;text-transform:uppercase}"
            ".hero-card .v{margin-top:10px;font-size:clamp(56px,6vw,78px);font-weight:700;line-height:.9;letter-spacing:-.06em;color:#0f172a}"
            ".mini{background:linear-gradient(180deg,#ffffff 0,#f8fbff 100%);border:1px solid #d8e3f1;border-radius:22px;padding:18px;box-shadow:var(--shadow);min-height:100%}"
            ".mini .k{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em}.mini .v{font-size:clamp(44px,4.8vw,62px);font-weight:700;line-height:.92;margin-top:8px;color:#0f172a}"
            ".panel{background:linear-gradient(180deg,#ffffff 0,#fbfdff 100%);border:1px solid var(--line);border-radius:22px;padding:18px;margin-bottom:16px;box-shadow:var(--shadow)}"
            ".filters-panel{margin-bottom:0;padding:0}"
            ".filters-shell{display:grid;grid-template-columns:minmax(0,1fr) 160px;gap:18px;align-items:start;padding:18px}"
            ".filters-fields{display:grid;grid-template-columns:1fr;gap:12px}"
            ".filters-actions{display:grid;grid-template-columns:1fr;gap:12px;align-content:start;padding-top:28px}"
            ".filters-actions .btn{width:100%}"
            ".filters{display:grid;grid-template-columns:1fr;gap:0;align-items:stretch}"
            "label{font-size:12px;color:#475569;display:block;margin-bottom:6px;font-weight:600;letter-spacing:.02em}"
            "select,input{width:100%;border:1px solid #cbd5e1;background:#f8fafc;border-radius:14px;padding:12px 13px;font-size:14px;color:var(--ink);outline:none;transition:border-color .2s,box-shadow .2s,transform .2s}"
            "select:focus,input:focus{border-color:#60a5fa;box-shadow:0 0 0 4px #dbeafe;transform:translateY(-1px)}"
            ".btn{padding:12px 16px;border:0;border-radius:14px;background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;font-weight:700;cursor:pointer;box-shadow:0 10px 24px rgba(37,99,235,.18);transition:transform .2s,box-shadow .2s,filter .2s}"
            ".btn:hover{transform:translateY(-1px);filter:saturate(1.05);box-shadow:0 14px 28px rgba(37,99,235,.22)}"
            ".btn.alt{background:#e2e8f0;color:#0f172a;box-shadow:none}"
            ".btn.alt:hover{background:#dbe4f0}"
            ".kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:14px 0 0 0}"
            ".kpi{background:linear-gradient(180deg,#ffffff 0,#f8fbff 100%);border:1px solid #d8e3f1;border-radius:18px;padding:14px 16px;box-shadow:var(--shadow)}"
            ".kpi .t{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;font-weight:700}"
            ".kpi .v{font-size:clamp(42px,5vw,58px);font-weight:700;line-height:.92;margin-top:8px;color:#081120}"
            ".grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}"
            "@media(max-width:1180px){body{padding:18px}.top-band{grid-template-columns:1fr}.hero{grid-template-columns:1fr 1fr 1fr}.grid{grid-template-columns:1fr}.filters-shell{grid-template-columns:1fr}.filters-actions{grid-template-columns:1fr 1fr 1fr;padding-top:0}}"
            ".chart{height:360px}"
            "table{width:100%;border-collapse:separate;border-spacing:0;font-size:13px;background:#fff;border:1px solid #d8e3f1;border-radius:16px;overflow:hidden}"
            "thead{background:linear-gradient(180deg,#f8fbff,#eef4fb)}"
            "th{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#334155}"
            "th,td{padding:11px 10px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top;color:#0f172a}"
            "tbody tr:nth-child(even){background:#f8fbff}"
            "tbody tr:hover{background:#edf4ff}"
            ".th-sort{display:flex;align-items:center;gap:8px}"
            ".sort-stack{display:inline-flex;flex-direction:column;line-height:1}"
            ".sort-btn{border:0;background:transparent;cursor:pointer;color:#2563eb;padding:0 2px;font-size:10px;height:10px}"
            "a{color:#2563eb;text-decoration:none;font-weight:600}a:hover{text-decoration:underline}"
            "#syncInfo{display:inline-block;padding-top:4px}"
            ".sync-updated{color:#8b9bb5;font-size:13px;font-weight:500}"
            "#marcas table,#anios table{font-size:12.5px}"
            "#tabla p{margin-bottom:0}"
            "</style>"
        )
        f.write("</head><body><div class='shell'><main class='content'>")
        f.write(f"<h1>Dashboard de stock</h1><p class='sub'>Panel limpio para revisar inventario, ordenar y filtrar rápido sin ruido visual</p>")
        f.write(
            "<section class='top-band'>"
            "<div class='hero'>"
            f"<div class='hero-card'><h3>Vehículos cargados</h3><div class='v'>{len(df):,}</div></div>"
            f"<div class='mini'><div class='k'>Marcas</div><div class='v'>{total_marcas}</div></div>"
            f"<div class='mini'><div class='k'>Modelos</div><div class='v'>{total_modelos}</div></div>"
            "</div>"
            "<div class='panel filters-panel'><div class='filters-shell'><div class='filters-fields'>"
            "<div><label>Marca</label><select id='fMarca'><option value=''>Todas</option>"
        )
        for marca in marcas:
            f.write(f"<option>{marca}</option>")
        f.write("</select></div>")
        f.write("<div><label>Modelo</label><select id='fModelo'><option value=''>Todos</option>")
        for modelo in modelos:
            f.write(f"<option>{modelo}</option>")
        f.write("</select></div>")
        f.write("<div><label>Año</label><select id='fAnio'><option value=''>Todos</option>")
        for anio in anios:
            f.write(f"<option>{anio}</option>")
        f.write("</select></div>")
        f.write(
            "</div><div class='filters-actions'>"
            "<div><button class='btn' id='aplicar'>Aplicar filtros</button></div>"
            "<div><button class='btn' id='actualizar'>Actualizar datos</button></div>"
            "<div><button class='btn alt' id='limpiar'>Limpiar</button></div>"
            "<div><small id='syncInfo' class='sync-updated'>actualizado</small></div>"
            "</div></div></div>"
        )

        f.write(
            "<div class='kpis'>"
            "<div class='kpi'><div class='t'>Vehículos filtrados</div><div class='v' id='kpiTotal'>0</div></div>"
            "</div>"
        )

        f.write(
            "<div class='panel'><h3 style='margin-top:0'>Detalle filtrado</h3><div id='tabla'></div></div>"
            "<div class='grid'>"
            "<div class='panel'><h3 style='margin:0 0 10px 0'>Unidades por marca</h3><div id='marcas'></div></div>"
            "<div class='panel'><h3 style='margin:0 0 10px 0'>Unidades por año</h3><div id='anios'></div></div>"
            "</div>"
        )

        js = """
<script>
const EMBEDDED_DATA = __EMBEDDED_DATA__;
let DATA = [...EMBEDDED_DATA];
const DATA_FILE = __DATA_FILE__;
const fmt = n => (n===null || n===undefined || n==='' || Number.isNaN(Number(n))) ? '-' : Number(n).toLocaleString('es-AR');
const money = n => (n===null || n===undefined || n==='' || Number.isNaN(Number(n))) ? '$ -' : '$ ' + Number(n).toLocaleString('es-AR');
const byId = id => document.getElementById(id);
const sortState = { col: '', dir: 'asc' };

function formatActualizado(date){
    const fecha = date.toLocaleDateString('es-AR');
    const hora = date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', hour12: false });
    return `actualizado ${fecha}, ${hora}`;
}

function setSyncInfo(msg){
    const el = byId('syncInfo');
    if (el){ el.textContent = msg; }
}

async function actualizarDatos(showAlert = true){
    try {
        const res = await fetch(`${DATA_FILE}?t=${Date.now()}`, { cache: 'no-store' });
        if (!res.ok){ throw new Error('HTTP ' + res.status); }
        const nuevos = await res.json();
        if (!Array.isArray(nuevos)){ throw new Error('JSON inválido'); }
        DATA = nuevos;
        syncModelos();
        renderAll();
        const stamp = new Date().toLocaleString('es-AR');
        setSyncInfo(formatActualizado(new Date()));
        if (showAlert){ alert('Datos actualizados correctamente.'); }
    } catch (err) {
        DATA = [...EMBEDDED_DATA];
        syncModelos();
        renderAll();
        setSyncInfo(formatActualizado(new Date()));
        if (showAlert){
            alert('No se pudo leer el archivo de datos externo. Si abrís el HTML con doble clic, usá un servidor local (python -m http.server) para actualizar sin regenerar.');
        }
    }
}

function syncModelos(){
    const marcaSel = byId('fMarca').value.trim().toLowerCase();
    const modeloSelect = byId('fModelo');
    const actual = modeloSelect.value;
    let modelos = [];
    if (!marcaSel){
        modelos = [...new Set(DATA.map(r => String(r.modelo || '').trim()).filter(Boolean))];
    } else {
        modelos = [...new Set(DATA.filter(r => String(r.marca || '').toLowerCase() === marcaSel).map(r => String(r.modelo || '').trim()).filter(Boolean))];
    }
    modelos.sort((a,b)=>a.localeCompare(b,'es',{sensitivity:'base'}));
    modeloSelect.innerHTML = '<option value="">Todos</option>' + modelos.map(m => `<option>${m}</option>`).join('');
    if (actual && modelos.includes(actual)){ modeloSelect.value = actual; }
}

function filtrar(){
    const marca = byId('fMarca').value.trim().toLowerCase();
    const modelo = byId('fModelo').value.trim().toLowerCase();
    const anioSel = byId('fAnio').value.trim();
    return DATA.filter(r => {
        const rm = String(r.marca || '').toLowerCase();
        const rmo = String(r.modelo || '').toLowerCase();
        const ranio = String(r.anio || '').trim();
        const okMarca = !marca || rm === marca;
        const okModelo = !modelo || rmo === modelo;
        const okAnio = !anioSel || ranio === anioSel;
        return okMarca && okModelo && okAnio;
    });
}

function renderKPIs(rows){
    byId('kpiTotal').textContent = rows.length.toLocaleString('es-AR');
}

function renderMarcas(rows){
    const m = {};
    rows.forEach(r => { const k = (r.marca || 'Sin marca'); m[k] = (m[k] || 0) + 1; });
    const pares = Object.entries(m).sort((a,b) => b[1] - a[1]);
    let html = '<table><thead><tr><th>Marca</th><th>Unidades</th></tr></thead><tbody>';
    for (const [marca, cant] of pares){ html += `<tr><td>${marca}</td><td>${fmt(cant)}</td></tr>`; }
    if (!pares.length){ html += '<tr><td colspan="2">Sin datos para los filtros actuales</td></tr>'; }
    html += '</tbody></table>';
    byId('marcas').innerHTML = html;
}

function renderAnios(rows){
    const m = {};
    rows.forEach(r => {
        const anio = Number(r.anio_num);
        const k = Number.isNaN(anio) ? 'Sin año' : String(anio);
        m[k] = (m[k] || 0) + 1;
    });
    const pares = Object.entries(m).sort((a,b) => {
        const an = Number(a[0]); const bn = Number(b[0]);
        const aNum = Number.isNaN(an) ? -Infinity : an;
        const bNum = Number.isNaN(bn) ? -Infinity : bn;
        return bNum - aNum;
    });
    let html = '<table><thead><tr><th>Año</th><th>Unidades</th></tr></thead><tbody>';
    for (const [anio, cant] of pares){ html += `<tr><td>${anio}</td><td>${fmt(cant)}</td></tr>`; }
    if (!pares.length){ html += '<tr><td colspan="2">Sin datos para los filtros actuales</td></tr>'; }
    html += '</tbody></table>';
    byId('anios').innerHTML = html;
}

function renderTabla(rows){
    const sorted = [...rows];
    if (sortState.col){
        const factor = sortState.dir === 'desc' ? -1 : 1;
        sorted.sort((a, b) => {
            const textCmp = (x, y) => String(x || '').localeCompare(String(y || ''), 'es', {sensitivity:'base'});
            if (sortState.col === 'anio'){
                const av = Number(a.anio_num); const bv = Number(b.anio_num);
                const an = Number.isNaN(av) ? -Infinity : av;
                const bn = Number.isNaN(bv) ? -Infinity : bv;
                return (an - bn) * factor;
            }
            if (sortState.col === 'kms'){
                const av = Number(a.kms_num); const bv = Number(b.kms_num);
                const an = Number.isNaN(av) ? -Infinity : av;
                const bn = Number.isNaN(bv) ? -Infinity : bv;
                return (an - bn) * factor;
            }
            if (sortState.col === 'precio'){
                const av = Number(a.precio_num); const bv = Number(b.precio_num);
                const an = Number.isNaN(av) ? -Infinity : av;
                const bn = Number.isNaN(bv) ? -Infinity : bv;
                return (an - bn) * factor;
            }
            return textCmp(a[sortState.col], b[sortState.col]) * factor;
        });
    }
    const top = sorted.slice(0, 300);
    const h = (label, key) => `<span class='th-sort'><span>${label}</span><span class='sort-stack'><button class='sort-btn' data-sort='${key}' data-dir='asc' title='Orden ascendente'>▲</button><button class='sort-btn' data-sort='${key}' data-dir='desc' title='Orden descendente'>▼</button></span></span>`;
    let html = `<table><thead><tr><th>Título</th><th>${h('Marca','marca')}</th><th>${h('Modelo','modelo')}</th><th>${h('Año','anio')}</th><th>${h('KMs','kms')}</th><th>${h('Precio','precio')}</th><th>${h('Link','link')}</th></tr></thead><tbody>`;
    for (const r of top){
        const kmsTxt = Number.isNaN(Number(r.kms_num)) ? (r.kms || '-') : fmt(r.kms_num);
        const precioTxt = Number.isNaN(Number(r.precio_num)) ? '$ -' : money(r.precio_num);
        const linkTxt = r.link ? `<a href='${r.link}' target='_blank'>ver</a>` : '-';
        html += `<tr><td>${r.titulo || '-'}</td><td>${r.marca || '-'}</td><td>${r.modelo || '-'}</td><td>${r.anio || '-'}</td><td>${kmsTxt}</td><td>${precioTxt}</td><td>${linkTxt}</td></tr>`;
    }
    html += '</tbody></table>';
    if (sorted.length > top.length){ html += `<p style="color:#5c6f82;font-size:12px">Mostrando ${top.length} de ${sorted.length} filas filtradas.</p>`; }
    byId('tabla').innerHTML = html;
}

function renderAll(){
    const rows = filtrar();
    renderKPIs(rows);
    renderMarcas(rows);
    renderAnios(rows);
    renderTabla(rows);
}

byId('aplicar').addEventListener('click', renderAll);
byId('actualizar').addEventListener('click', () => actualizarDatos(true));
byId('limpiar').addEventListener('click', () => {
    byId('fMarca').value = ''; byId('fModelo').value = ''; byId('fAnio').value = '';
    sortState.col = ''; sortState.dir = 'asc';
    syncModelos();
    renderAll();
});
byId('tabla').addEventListener('click', (ev) => {
    const target = ev.target;
    if (target && target.classList.contains('sort-btn')){
        sortState.col = target.dataset.sort || '';
        sortState.dir = target.dataset.dir || 'asc';
        renderAll();
    }
});
byId('fMarca').addEventListener('change', () => { syncModelos(); renderAll(); });
byId('fModelo').addEventListener('change', renderAll);
byId('fAnio').addEventListener('change', renderAll);
syncModelos();
renderAll();
actualizarDatos(false);
</script>
"""
        js = js.replace("__EMBEDDED_DATA__", json.dumps(datos_json, ensure_ascii=False))
        js = js.replace("__DATA_FILE__", json.dumps(data_filename, ensure_ascii=False))
        f.write(js)
        f.write("</main></div></body></html>")

    print(f"Dashboard guardado en {salida}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera un dashboard HTML a partir del CSV del scraper de vehículos")
    parser.add_argument("csv", help="Archivo CSV generado por meli_vehiculos_scraper.py")
    parser.add_argument("--salida", default="dashboard.html", help="Nombre del archivo HTML de salida")
    args = parser.parse_args()

    df = cargar(args.csv)
    armar_dashboard(df, args.salida)