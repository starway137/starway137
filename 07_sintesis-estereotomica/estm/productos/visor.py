"""Visor 3D interactivo autocontenido (un solo .html, abre en cualquier navegador).

- Órbita (arrastrar), zoom (rueda), encuadre (doble clic).
- Deslizador de montaje: muestra las piezas hasta el paso k de la secuencia.
- Capas por tipo de pieza; vista de gusano (desde abajo) o desde arriba.
- Clic sobre una pieza: id, tipo, masa, método de fabricación recomendado.
three.js r128 desde cdnjs; la geometría va incrustada en el propio archivo.
"""

import json
from pathlib import Path

from .mallas import color, triangulos

PLANTILLA = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITULO__</title>
<style>
:root{--bg:#f4f1ea;--fg:#2b2622;--panel:#fffdf8cc;--borde:#d9d1c3}
@media (prefers-color-scheme:dark){:root{--bg:#1d1b19;--fg:#ece6dc;--panel:#2a2724cc;--borde:#4a443d}}
html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,sans-serif}
#lienzo{position:fixed;inset:0}
#panel{position:fixed;top:12px;left:12px;max-width:min(340px,calc(100vw - 48px));background:var(--panel);
 border:1px solid var(--borde);border-radius:10px;padding:12px 14px;backdrop-filter:blur(6px)}
#panel h1{font-size:15px;margin:0 0 4px}#panel p{margin:2px 0 8px;opacity:.8}
label{display:flex;gap:6px;align-items:center;margin:2px 0}input[type=range]{width:100%}
.sw{width:12px;height:12px;border-radius:3px;display:inline-block}
#info{position:fixed;bottom:12px;left:12px;right:12px;max-width:520px;background:var(--panel);
 border:1px solid var(--borde);border-radius:10px;padding:8px 12px;font-variant-numeric:tabular-nums}
button{font:inherit;border:1px solid var(--borde);background:transparent;color:inherit;border-radius:6px;padding:3px 8px}
</style></head><body>
<canvas id="lienzo"></canvas>
<div id="panel"><h1>__TITULO__</h1><p>__SUBTITULO__</p>
<label>Montaje: <span id="paso"></span></label><input id="montaje" type="range" min="0" value="0">
<div id="capas"></div>
<p><button id="vista">Ver desde arriba</button> <button id="encuadre">Encuadrar</button></p></div>
<div id="info">Arrastra para girar · rueda para acercar · clic en una pieza para ver sus datos</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const D = __DATOS__;
const lienzo = document.getElementById('lienzo');
const ren = new THREE.WebGLRenderer({canvas: lienzo, antialias: true, alpha: true});
ren.setPixelRatio(Math.min(devicePixelRatio, 2));
const escena = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(40, 1, 0.05, 2000);
cam.up.set(0, 0, 1);
escena.add(new THREE.HemisphereLight(0xffffff, 0x6b5f50, 0.85));
const sol = new THREE.DirectionalLight(0xffffff, 0.6); sol.position.set(-3, -4, 6); escena.add(sol);
const mats = {}, grupos = {}, mallas = [];
for (const t of D.tipos) { mats[t.tipo] = new THREE.MeshLambertMaterial({color: new THREE.Color(...t.rgb.map(c => c / 255)), side: THREE.DoubleSide});
  grupos[t.tipo] = new THREE.Group(); escena.add(grupos[t.tipo]); }
const lineas = new THREE.LineBasicMaterial({color: 0x3a3029, transparent: true, opacity: 0.35});
for (const p of D.piezas) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(p.P, 3)); g.computeVertexNormals();
  const m = new THREE.Mesh(g, mats[p.tipo]); m.userData = p;
  m.add(new THREE.LineSegments(new THREE.EdgesGeometry(g, 20), lineas));
  grupos[p.tipo].add(m); mallas.push(m);
}
const caja = new THREE.Box3(); mallas.forEach(m => caja.expandByObject(m));
const centro = caja.getCenter(new THREE.Vector3()), radio = caja.getSize(new THREE.Vector3()).length() / 2;
let az = -0.6, el = -0.55, dist = radio * 2.6;
function colocar() { cam.position.set(centro.x + dist * Math.cos(el) * Math.cos(az), centro.y + dist * Math.cos(el) * Math.sin(az),
  centro.z + dist * Math.sin(el)); cam.lookAt(centro); }
function tam() { const w = innerWidth, h = innerHeight; ren.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); }
addEventListener('resize', () => { tam(); dibujar(); });
let arr = null, movido = false;
lienzo.addEventListener('pointerdown', e => { arr = [e.clientX, e.clientY]; movido = false; lienzo.setPointerCapture(e.pointerId); });
lienzo.addEventListener('pointermove', e => { if (!arr) return; const dx = e.clientX - arr[0], dy = e.clientY - arr[1];
  if (Math.abs(dx) + Math.abs(dy) > 2) movido = true; az -= dx * 0.008; el = Math.max(-1.5, Math.min(1.5, el + dy * 0.008));
  arr = [e.clientX, e.clientY]; colocar(); dibujar(); });
lienzo.addEventListener('pointerup', e => { arr = null; if (!movido) elegir(e); });
lienzo.addEventListener('wheel', e => { e.preventDefault(); dist *= Math.exp(e.deltaY * 0.001); colocar(); dibujar(); }, {passive: false});
lienzo.addEventListener('dblclick', () => { dist = radio * 2.6; colocar(); dibujar(); });
const ray = new THREE.Raycaster(), info = document.getElementById('info');
let marcada = null;
function elegir(e) {
  ray.setFromCamera(new THREE.Vector2(e.clientX / innerWidth * 2 - 1, -e.clientY / innerHeight * 2 + 1), cam);
  const h = ray.intersectObjects(mallas.filter(m => m.visible && m.parent.visible), false)[0];
  if (marcada) marcada.material = mats[marcada.userData.tipo];
  if (!h) { info.textContent = 'Sin pieza bajo el cursor'; marcada = null; dibujar(); return; }
  marcada = h.object; marcada.material = new THREE.MeshLambertMaterial({color: 0xd23c2c, side: THREE.DoubleSide});
  const u = marcada.userData;
  info.textContent = `${u.id} · ${u.tipo} · ${u.masa_kg} kg · montaje nº ${u.orden} · fabricación: ${u.metodo || '—'}`;
  dibujar();
}
const rango = document.getElementById('montaje'), paso = document.getElementById('paso');
rango.max = D.piezas.length; rango.value = D.piezas.length;
rango.addEventListener('input', () => { const k = +rango.value; mallas.forEach(m => m.visible = m.userData.orden < k);
  paso.textContent = `${k} / ${D.piezas.length} piezas`; dibujar(); });
paso.textContent = `${D.piezas.length} / ${D.piezas.length} piezas`;
const capas = document.getElementById('capas');
for (const t of D.tipos) { const l = document.createElement('label');
  l.innerHTML = `<input type="checkbox" checked> <span class="sw" style="background:rgb(${t.rgb})"></span> ${t.tipo} (${t.n})`;
  l.querySelector('input').addEventListener('change', e => { grupos[t.tipo].visible = e.target.checked; dibujar(); }); capas.appendChild(l); }
document.getElementById('vista').addEventListener('click', e => { el = -el; e.target.textContent = el < 0 ? 'Ver desde arriba' : 'Ver desde abajo'; colocar(); dibujar(); });
document.getElementById('encuadre').addEventListener('click', () => { dist = radio * 2.6; colocar(); dibujar(); });
function dibujar() { ren.render(escena, cam); }
tam(); colocar(); dibujar();
</script></body></html>
"""


def visor(obra, ruta, subtitulo=""):
    g = obra.grafo
    piezas, tipos = [], {}
    for nid in g.piezas():
        d, geo = g.nodos[nid], g.geometrias[nid]
        T = triangulos(geo)
        piezas.append({"id": nid, "tipo": d["tipo"], "orden": int(d.get("orden_montaje", 0)),
                       "masa_kg": round(d.get("masa_kg", 0.0), 1), "metodo": d.get("metodo_recomendado", ""),
                       "P": [round(float(v), 4) for v in geo.V[T.ravel()].ravel()]})
        tipos[d["tipo"]] = tipos.get(d["tipo"], 0) + 1
    datos = {"piezas": piezas, "tipos": [{"tipo": t, "n": n, "rgb": list(color(t))} for t, n in sorted(tipos.items())]}
    html = (PLANTILLA.replace("__TITULO__", f"{obra.id} · visor de piezas")
            .replace("__SUBTITULO__", subtitulo or obra.nombre)
            .replace("__DATOS__", json.dumps(datos, separators=(",", ":"))))
    Path(ruta).write_text(html, encoding="utf-8")
    return [Path(ruta)]

