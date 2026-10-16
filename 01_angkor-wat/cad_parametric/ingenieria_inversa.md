# Angkor Wat — ingeniería inversa paramétrica

## 1. Regla generativa reconstruida

```
ENTRADA: centro C, eje E-O dirigido a poniente, módulo hat
1. Foso:        rectángulo L0 × L0/a0, anchura de agua w
2. Recinto:     rectángulo concéntrico, muro de laterita h = 4.5 m
3. Para k = 2..4 (terrazas):
       L_k = L_(k-1) · r_k        (r_k ≈ 0.5 en el régimen arquitectónico)
       terraza maciza de altura h_k, galería perimetral sobre ella
4. Quincunce:   torre central sobre el centro + 4 torres en las esquinas de la plataforma superior
5. Eje:         calzada continua desde el foso hasta el templo por el lado oeste
```

Parámetros libres: `L0`, `a` (aspecto), `r_k`, `h_k`, dimensiones de torres y
anchura de galerías. Todos están en `parametros.json`; los marcados C son
hipótesis de reconstrucción.

## 2. Restricciones deducidas

| Restricción | Valor / regla | Efecto en la forma |
|---|---|---|
| Bóveda en saledizo de arenisca | Luz útil de pocos metros | Galerías estrechas (4–6 m), alargadas |
| Bloques sin mortero | Estabilidad por peso y trabazón | Torres macizas escalonadas; factor de volumen ~0.45 |
| Subsuelo arenoso, freático variable | σ_base ≈ 0.16 MPa | Huella amplia y masa repartida en terrazas; foso regulador |
| Transporte de piedra por canal | ~40 km desde Phnom Kulen | Arenisca reservada a revestimiento y piezas vistas; núcleos de laterita y arena |
| Orientación ritual | Frente a poniente | Calzada occidental larga; secuencia de ascenso este |

## 3. Secuencia constructiva hipotética

1. Excavación del foso y uso del material como terraplén (balance de tierras).
2. Compactación de la plataforma de arena y núcleos de laterita.
3. Levantamiento de terrazas de dentro afuera o por anillos simultáneos (la susceptibilidad magnética de los bloques permite fecharlos por fases; Uchida et al.).
4. Revestimiento y talla de bajorrelieves in situ.

## 4. Salidas del modelo

| Archivo | Contenido |
|---|---|
| `salida/angkor_wat_planta.svg` | Planta cenital con ejes, escala y norte |
| `salida/angkor_wat_volumetria.obj` | Volumetría importable (Rhino, Blender, SketchUp) |
| `salida/angkor_wat_geometria.json` | Primitivas, volúmenes y cómputos de contraste |

## 5. Contrastes y lo que haría falta para cerrarlos

| Hipótesis | Resultado del modelo | Dato necesario para cerrarla |
|---|---|---|
| AW-H1 | r = 0.42 (R² 0.96) en el régimen arquitectónico | Planta LiDAR georreferenciada |
| AW-H2 | 1722 hat vs 1728 hat (−0.3 %) | Puntos de medida pre-registrados + levantamiento A |
| AW-H3 | Ángulo visual de la torre 7.2° desde la puerta oeste | Azimut del eje medido en ortofoto |
| AW-H4 | σ_base = 0.16 MPa | Ensayos geotécnicos y registro de asientos |
