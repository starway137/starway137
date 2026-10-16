# Fundamentos del pipeline ESTM

## 1. Representación: grafo atribuido relacional G = (V, E)

Cada obra es un grafo cuyos **nodos** son piezas de fábrica (o apoyos) y cuyas
**aristas** son relaciones constructivas, no simples adyacencias geométricas.

| Nodo `tipo` | Significado | Atributos principales |
|---|---|---|
| `dovela` | dovela de arco | volumen, masa, centroide, caja orientada, inclinación de junta |
| `dovela_nervio` | dovela de nervio (juntas normales a la directriz) | familia (crucería, tercelete, ligadura, formero) |
| `clave` | clave de cierre o de cruce de nervios | — |
| `jarja` | arranque de nervios en el vértice | vértice |
| `plemento` | pieza de plementería / cáscara | sector, hilada |
| `celda_mocarabe` | celda volada con lechos horizontales | nivel, matajunta |
| `apoyo` | pilar (vértice) o muro/tambor (lado) | soporte |

| Arista `tipo` | Significado | Atributos |
|---|---|---|
| `junta_radial` | junta normal al intradós | área, normal, inclinación |
| `lecho` | lecho entre hiladas | área, normal, inclinación |
| `junta_lateral` | junta dentro de la hilada | área, normal |
| `voladizo` | celda que vuela sobre la hilada inferior | área del solape |
| `apoyo_nervio` | plemento que descansa en un nervio | — |
| `encuentro_clave`, `arranque`, `apoyo` | acometidas a claves, jarjas y apoyos | — |

El área, la normal y la inclinación de cada junta se calculan sobre la cara
compartida real (o sobre el solape exacto entre hiladas con distinto número de
piezas). La geometría de cada pieza es un poliedro cerrado con volumen y
centroide exactos (divergencia sobre caras trianguladas).

## 2. Gramática paramétrica unificada

Un **genoma de 10 parámetros** con significado constructivo describe arcos,
crucerías, estrelladas, nervadas califales, mocárabes y sus híbridos:

| Gen | Rango | Significado |
|---|---|---|
| `orden_radial` | 4–12 (par) | lados del polígono de planta |
| `salto_estrella_rel` | 0–0.5 | nervios según el polígono estrellado {n/k}, k = rel·n |
| `terceletes` | 0/1 | terceletes y ligaduras con claves secundarias |
| `apuntamiento` | 0–1 | 0 medio punto → 1 apuntado equilátero (traza con compás) |
| `beta_superficie` | 0–1 | 0 bóveda de arista → 1 cúpula / paños |
| `espesor_rel` | 0.012–0.10 | espesor / luz |
| `mocarabe_rel` | 0–0.9 | fracción radial ocupada por celdas voladas |
| `inclinacion_junta` | 0–1 | 0 lechos horizontales (voladizo) → 1 juntas normales (dovelas) |
| `despiece` | 6–14 | número de hiladas (tamaño de pieza) |
| `canto_nervio_rel` | 0–0.06 | canto de nervio / luz |

`inclinacion_junta` es el gen que conecta físicamente las tradiciones: el paso
de la **estereotomía de dovelas** (juntas normales, trabajan como arco y
necesitan cimbra) a la **construcción por voladizo** (lechos horizontales,
mocárabes, falsas cúpulas) cambia el mecanismo resistente, y la verificación
lo detecta.

## 3. Verificación por el límite inferior (Heyman)

Hipótesis de Heyman (1966): resistencia a compresión ilimitada, tracción nula
y ausencia de deslizamiento. **Teorema de la seguridad:** si se encuentra una
distribución de esfuerzos en equilibrio contenida en la fábrica, la estructura
es segura. Los métodos buscan esa distribución. Que no la encuentren no prueba
el colapso: el resultado es siempre conservador.

| Método | Aplicación | Qué hace |
|---|---|---|
| `arco` | arcos | Línea de empujes del semiarco: barrido (H, punto de paso en la clave), corte de la resultante con cada junta (cualquier orientación) |
| `cortes` | arista / crucería (β < 0.5) | Heyman: plementería cortada en franjas-arco entre nervios; cada franja con su línea de empujes; nervios diagonales cargados con el peso y el empuje proyectado de las franjas |
| `rebanada` | cúpulas (β ≥ 0.5) | Gajo por la bisectriz del sector con anchura variable; ignora los anillos (muy conservador) |
| `tna` | todas las bóvedas | Thrust Network Analysis (Block 2009): diagrama de forma de arista en equilibrio horizontal exacto, alturas por densidades de fuerza (Schek 1974) y optimización Nelder-Mead del diagrama de fuerzas maximizando la holgura en la fábrica |
| `tna_anillos` | cúpulas | TNA con meridianos y anillos de compresión (sin tracción) y apoyo perimetral |

**Coeficiente geométrico de seguridad (GSF):** cociente entre el espesor real
y el espesor mínimo con solución admisible (bisección). Opcionalmente se
comprueba el no-deslizamiento con μ = 0.7.

**Validación del solver:** el arco de medio punto con juntas radiales da
t/R = 0.1081, frente al valor clásico de 0.1075 (Milankovitch 1907; Heyman
1969). Es estable con 30, 90 y 180 dovelas, y la prueba exige 0.1075 ± 0.004
(`tests/test_estm.py`).

**Rellenos y estribos:** el relleno de senos se incluye como carga y como
envolvente por la que puede pasar la red. Con las reacciones del método
admisible se comprueba el vuelco de un estribo de referencia (ancho 0.30 L,
fondo 0.15 L, arranque a 1.2 L).

### Lo que estos métodos no encuentran (y por qué)

- **TNA con el diagrama de arista:** en las crucerías no encuentra red. Obliga
  a que el empuje del plemento entre en el nervio a la altura de la red del
  nervio. El método de los cortes, que permite que entre en cualquier punto de
  la sección, sí encuentra solución. Con un único diagrama de forma la TNA es
  menos flexible que el corte manual.
- **Estrellada (GO-EST, GSF 0.98) y mocárabes (NA-MOC, GSF 0.94):** les falta
  un 2–6 % de espesor con los métodos conservadores. Los cortes ignoran el
  bombeo de la plementería y la colaboración de rellenos y muros; la rebanada
  ignora los anillos. No es una prueba de inseguridad. Además, los mocárabes
  de la Alhambra son de yeso colgado y no portantes: la versión analizada es
  hipotética, en fábrica.

## 4. Fabricación digital (DfAM)

| Ruta | Reglas |
|---|---|
| Piedra CNC | envolvente 3.5 × 2.0 × 1.5 m · masa ≤ 6 t · aprovechamiento del bloque ≥ 25 % · planeidad de juntas ≤ 3 mm · diedro ≥ 35° |
| 3DCP | envolvente 2.5 × 2.5 × 2.0 m · voladizo ≤ 25° con la mejor de 8 orientaciones de impresión · espesor ≥ 2 cordones (0.08 m) · diedro ≥ 20° |

La regla de **planeidad de juntas** es estereotómica: las juntas alabeadas que
produce una superficie de doble curvatura no se pueden labrar con disco y el
pipeline las señala. La **secuencia de montaje** recorre el grafo desde los
apoyos y marca `requiere_cimbra` en piezas de juntas radiales.

## 5. Patrones y aprendizaje continuo

- **Firmas de patrón:** etiquetado Weisfeiler-Lehman (2 iteraciones) sobre los
  tipos de pieza y de junta, con hashing a 64 dimensiones más 12 autovalores
  del laplaciano normalizado. Da la similitud entre obras.
- **Descriptor de pieza (13 dimensiones):** volumen, esbeltez, inclinación de
  junta, grado, altura relativa y composición de tipos de junta. Las escalas
  son fijas y no dependen del corpus.
- **Diccionario con memoria episódica** (`estm/memoria.py`). Cada obra es un
  episodio. Garantías verificadas por las pruebas:
  1. Las anclas de prototipo se congelan al crearse: lo aprendido no deriva.
  2. Los estadísticos (n, media, M2) son exactos y se combinan con la fórmula
     de Chan.
  3. Antes de crear un ancla se comprueba contra la memoria episódica; si
     cambiaría la clasificación de algún recuerdo, no se crea. Así la
     retención es 1.000 por construcción.
  4. El registro de eventos es de solo añadir, con precisión completa, y el
     estado se reconstruye idéntico reproduciéndolo.

Es aprendizaje incremental por prototipos con repaso: interpretable y
verificable, no una red neuronal.

## 6. Síntesis propositiva por interpolación esférica

El genoma se normaliza a [-1, 1] con cotas fijas. Entre dos tradiciones:

$$z(t) = \operatorname{slerp}(\hat z_a, \hat z_b, t)\,\big((1-t)\lVert z_a\rVert + t\lVert z_b\rVert\big)$$

La dirección se interpola sobre la hiperesfera y la norma linealmente. Así se
conserva la intensidad de los rasgos a mitad de camino; la media lineal de dos
genomas opuestos colapsaría hacia una obra genérica (lo comprueba
`test_slerp_extremos_y_norma`). Los genes discretos se redondean a valores
válidos (n par, k ≤ n/2).

Cada híbrido se genera y se verifica. Si no alcanza GSF ≥ 1.5, se le aplica la
**reparación mínima** (espesor × 1.25 por paso, como máximo 5 pasos). Después
se ingiere como episodio nuevo, de modo que el diccionario aprende las
tradiciones híbridas sin olvidar las históricas.

## Referencias

- Heyman, J. (1966). The stone skeleton. *Int. J. Solids Structures* 2, 249–279; (1995) *The Stone Skeleton*, CUP.
- Heyman, J. (1969). The safety of masonry arches. *Int. J. Mech. Sci.* 11, 363–385.
- Milankovitch, M. (1907). Theorie der Druckkurven. *Zeitschrift für Mathematik und Physik* 55, 1–27.
- Block, P. (2009). *Thrust Network Analysis*. PhD thesis, MIT.
- Block, P. & Lachauer, L. (2014). Three-dimensional funicular analysis of masonry vaults. *Mech. Res. Comm.* 56, 53–60.
- Schek, H.-J. (1974). The force density method for form finding. *Comp. Meth. Appl. Mech. Eng.* 3, 115–134.
- Huerta, S. (2004). *Arcos, bóvedas y cúpulas*. Instituto Juan de Herrera.
- Shervashidze, N. et al. (2011). Weisfeiler-Lehman graph kernels. *JMLR* 12, 2539–2561.
- Chan, T., Golub, G. & LeVeque, R. (1979). Updating formulae and a pairwise algorithm for computing sample variances.
- Shoemake, K. (1985). Animating rotation with quaternion curves (slerp). *SIGGRAPH*.
