# Síntesis cruzada — patrones comunes y divergencias

> Las cifras proceden de [`resultados_modelos.md`](resultados_modelos.md)
> (generado). Este documento las interpreta; si los datos cambian, revisar
> la interpretación contra el archivo generado.

## 1. Matriz comparativa

| Dimensión | Angkor Wat | Kailasa | Ayutthaya (W. Chaiwatthanaram) | Mohenjo-daro | Sanchi |
|---|---|---|---|---|---|
| Patrón | Concéntrico rectangular | Axial lineal | Quincunce en recinto | Retícula ortogonal | Radial concéntrico |
| Simetría | D2 (núcleo ≈ D4) | D1 | D2 (núcleo ≈ D4) | p2mm (traslación) | **C4 quiral** |
| Proceso | Aditivo | **Sustractivo** | Aditivo | Aditivo modular | Encapsulamiento |
| Frente | Oeste (dirigido) | Oeste (dirigido) | Este (dirigido) | No dirigido | 4 cardinales |
| r de anidamiento (R²) | 0.40 (0.98) | 0.39 (0.97) | 0.44 (0.99) | **0.13** (0.96) | 0.35 (0.92) |
| Esbeltez masa principal | 0.32 | 1.67 | **2.33** | 0.04 | 0.51 |
| σ base (MPa) | 0.16 | 0.34 | 0.25 | 0.17 | 0.21 |
| FS (f_c mín.) | 124 | **293** | 20 | **5.9** | 15 |
| Fracción de ocupación | **0.06** | 0.44 | 0.35 | **0.70** | 0.69 |
| Porosidad de alzados | 0.35 | 0.15 | 0.20 | 0.08 | 0.02 |

## 2. Patrones comunes (invariantes del corpus)

1. **Anidamiento geométrico.** Los cinco casos admiten una cadena de inclusión
   bien descrita por L_k = L_0 · r^k (R² ≥ 0.92 en todos). En los cuatro
   casos con centro sagrado, r se concentra en **0.35–0.44** (media
   geométrica de los cinco: 0.31). Regla práctica: *cada recinto mide entre un
   tercio y la mitad del que lo contiene*. Es el invariante más robusto del
   dataset y el principal prior generativo.
2. **Tensiones bajas, formas no limitadas por resistencia.** Todas las masas
   trabajan entre 0.08 y 0.43 MPa de tensión media, con FS entre 6 y 544. La
   forma la gobiernan la estabilidad, el proceso y el terreno (Heyman 1995),
   no la resistencia del material.
3. **Eje dominante.** Cuatro de cinco casos tienen un eje dirigido o
   cuaternario que organiza el acceso; solo la retícula de Mohenjo-daro es
   isótropa.
4. **El agua como límite.** Foso (Angkor), río e isla (Ayutthaya), drenaje y
   estanque (Mohenjo-daro): la hidráulica define el borde en tres casos.

## 3. Divergencias geométricas

| Divergencia | Polo A | Polo B | Variable que la captura |
|---|---|---|---|
| Masa frente a vacío | Angkor (0.06: masa concentrada en un campo vacío) | Mohenjo-daro / Sanchi (≈ 0.7) | `fraccion_ocupacion` |
| Vertical frente a horizontal | Ayutthaya (prang, esbeltez 2.33) | Mohenjo-daro (plataforma, 0.04) | `esbeltez_masa_principal` |
| Aditivo frente a sustractivo | Angkor, Ayutthaya | Kailasa | `proceso_constructivo` |
| Central frente a reticular | Angkor, Sanchi | Mohenjo-daro | `grupo_simetria`, `razon_anidamiento_r` |
| Quiralidad | Sanchi (C4, sin reflexión) | Resto (con reflexión) | `simetria_reflexion` |
| Gradiente de escala | Mohenjo-daro (r = 0.13: de la ciudad al ladrillo) | Ayutthaya (r = 0.44) | `razon_anidamiento_r` |

## 4. Linajes y transferencias

- **Angkor → Ayutthaya:** la regla del quincunce en recinto se transfiere con
  la misma razón entre recintos sucesivos (0.52–0.53) pero se verticaliza
  (escala de altura 0.54 frente a escala lineal 0.35). La topología viaja; la
  métrica se adapta al material (ladrillo) y al programa.
- **Kailasa ↔ Sanchi:** dos montañas cósmicas (Kailasa/Meru y axis mundi)
  resueltas con procesos opuestos: retirar materia (Kailasa) frente a envolver
  materia (Sanchi).
- **Mohenjo-daro como control:** demuestra que el anidamiento aparece también
  sin cosmograma, como consecuencia de una norma constructiva que se repite a
  través de la escala.

## 5. Proporciones canónicas: resultado negativo explícito

Ninguno de los cinco casos aporta evidencia estadística de proporción áurea.
Con 11 cánones candidatos y tolerancia ±2 %, cualquier razón aleatoria tiene
un 35 % de probabilidad de "coincidir" con alguno. Las coincidencias exactas
del dataset (3:2 de la manzana harappana, 2:1 de la isla de Ayutthaya) se
deben a medidas redondeadas de calidad C. El invariante real no es un canon
sino la **constancia del aspecto a través de la escala** (Angkor: 1.15 en tres
niveles) y la **razón de anidamiento**.

## 6. Límites de la síntesis

- n = 5 obras de cuatro tradiciones; 39 elementos medidos, de los cuales una
  parte relevante es de calidad C.
- Las estimaciones de masa/vacío y porosidad son lecturas de planta y deben
  sustituirse por mediciones sobre ortofoto, LiDAR o fotogrametría.
- Las relaciones descritas son regularidades del corpus, no leyes causales.
