# Angkor Wat — patrones, simetrías y proporciones

> Cifras calculadas por el pipeline (`data/features.json`,
> `cad_parametric/salida/angkor_wat_geometria.json`). Si cambian los datos,
> manda el archivo generado.

## 1. Patrón compositivo: anidamiento concéntrico rectangular

| Nivel k | Elemento | Dimensión mayor (m) | Razón L_k / L_(k-1) | Aspecto L/A |
|---|---|---|---|---|
| 0 | Foso (contorno exterior) | 1500 | — | 1.154 |
| 1 | Recinto exterior | 1024 | 0.68 | 1.277 |
| 2 | Tercera galería | 215 | 0.21 | 1.150 |
| 3 | Segunda galería | 115 | 0.53 | 1.150 |
| 4 | Plataforma central (Bakan) | 60 | 0.52 | 1.000 |
| 5 | Torre central | 15 | 0.25 | 1.000 |

- Ajuste exponencial sobre toda la cadena: **r = 0.399** (IC95 0.33–0.49), R² = 0.98.
- Solo el régimen arquitectónico (niveles 2–5): **r = 0.42**, R² = 0.96. Las dos galerías intermedias muestran una razón casi constante (0.53, 0.52): cada recinto mide la mitad del que lo contiene.
- El salto 0.21 entre recinto y templo separa dos regímenes: el **territorial** (foso + recinto, ~1 km) y el **arquitectónico** (galerías + torres, ~200 m). Es el resultado central para AW-H1.

## 2. Autosemejanza de la proporción

El aspecto se conserva en tres niveles no consecutivos: foso 1.154, tercera
galería 1.150, segunda galería 1.150. La constancia del aspecto a través de la
escala es una regla generativa más robusta que cualquier canon individual:
define la familia de rectángulos y deja libre solo el factor de escala.

Coincide numéricamente con 2/√3 = 1.1547, pero no se interpreta: con 11
cánones candidatos y tolerancia ±1 %, la probabilidad de una coincidencia por
azar es 0.18 (`archimorph/canons.py`).

## 3. Cánones de proporción (con control de azar)

| Razón | Valor | Canon más próximo | Desviación |
|---|---|---|---|
| Recinto exterior 1024 / 802 | 1.277 | 5:4 | +2.1 % |
| Foso 1500 / 1300 | 1.154 | 5:4 | −7.7 % |
| Tercera galería 215 / 187 | 1.150 | 5:4 | −8.0 % |
| Altura / galería III 65 / 215 | 0.302 | — | — |

Con tolerancia ±2 %, la probabilidad de caer cerca de algún canon por azar es
**0.35**. Ninguna razón de Angkor Wat permite afirmar el uso de la sección
áurea; la proporción áurea atribuida en la divulgación no se sostiene con
estas medidas.

## 4. Simetría

- Grupo en planta **D2** (dos ejes de reflexión, rotación de orden 2) a escala de recinto.
- El núcleo (quincunce sobre plataforma cuadrada) se aproxima a **D4**.
- La simetría se rompe en el eje oeste (calzada, acceso principal): el edificio es **dirigido** (azimut del frente 270°). Vector axial invariante: cos(2θ) = −1, sin(2θ) = 0.

## 5. Modulación espacial

| Medida | m | hat (0.43545 m) |
|---|---|---|
| Recinto exterior (largo) | 1024 | 2352 |
| Tercera galería (largo) | 215 | 494 |
| Altura total | 65 | 149 |
| Borde oeste del foso → torre central | 750 | **1722** |

El valor 1722 hat queda a −0.3 % de los 1728 hat propuestos por Stencel et al.
(1976) como codificación del Krita Yuga (AW-H2). La coincidencia es notable pero
**no concluyente**: el punto de medida se eligió a posteriori en la literatura y
la dimensión del foso es aproximada (±5 %).

## 6. Distribución de masas y vanos

- Fracción de ocupación del recinto exterior: **0.06** (C). Angkor Wat es sobre todo vacío: un gran campo ceremonial con una masa concentrada.
- Porosidad de alzados en galerías con pilares: **0.35** (C), la mayor del dataset.
- Factor de volumen del templo-montaña: **0.107** — solo el 11 % de la envolvente (215 × 187 × 65 m) es macizo.
- Tensión media de peso propio sobre la huella: **0.16 MPa**, FS ≈ 124 respecto de la arenisca. El orden de magnitud coincide con la capacidad portante de arenas medias: la restricción activa es el terreno (AW-H4).

## 7. Descriptores para ML

Ver `data/features.json`. Etiquetas: `recintos_concentricos`, `quincunce`,
`eje_ceremonial_largo`, `terrazas_escalonadas`, `foso_cosmologico`,
`alineacion_equinoccial`.
