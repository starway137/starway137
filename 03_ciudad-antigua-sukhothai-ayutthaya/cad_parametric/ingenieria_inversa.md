# Wat Chaiwatthanaram — ingeniería inversa paramétrica

## 1. Regla generativa reconstruida

```
ENTRADA: frente fluvial a levante, módulo wa (2 m)
1. Galería rectangular G (76 × 68 m) con 8 meru thit en esquinas y puntos medios.
2. Plataforma cuadrada P = 0.53 · G, maciza, h = 5 m.
3. Quincunce sobre P: prang central (base 0.375 · P, H = 35 m) + 4 prangs de esquina (base 0.47 · central).
4. Ubosot sobre el eje este, entre la galería y el río.
```

Comparada con Angkor Wat, la regla elimina el régimen territorial (no hay foso
propio: el río ejerce esa función) y comprime la cadena arquitectónica a tres
niveles, con un núcleo más alto en proporción.

## 2. Restricciones deducidas

| Restricción | Efecto en la forma |
|---|---|
| Ladrillo + estuco (sin sillería) | Masas con FS menores (≈ 20); revestimiento como capa de sacrificio |
| Inundación anual | Plataforma maciza; acceso por el río |
| Cita política del modelo jemer | Quincunce explícito, prangs de perfil jemer verticalizado |
| Programa theravada | Ubosot en el eje, galería con imágenes de Buda |

## 3. Salidas del modelo

| Archivo | Contenido |
|---|---|
| `salida/wat_chaiwatthanaram_planta.svg` | Galería, merus, plataforma, quincunce, ubosot y orilla |
| `salida/wat_chaiwatthanaram_volumetria.obj` | Volumetría |
| `salida/wat_chaiwatthanaram_geometria.json` | Primitivas, proporciones adimensionales y test AY-H1 |

## 4. Para cerrar las hipótesis

- Digitalizar la planta sobre ortofoto (galería, plataforma, prangs) → pasar las medidas a calidad A/B.
- Levantar el perfil del prang central para estimar su factor de volumen real.
- SIG del perímetro insular de Ayutthaya (AY-H2) y del recinto de Sukhothai (AY-H4).
