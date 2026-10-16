# Templo de Kailasa — ingeniería inversa sustractiva

## 1. Regla generativa reconstruida

```
ENTRADA: ladera basáltica con pendiente hacia poniente
1. Trazar en la cima el rectángulo del patio (82 × 46 m) alineado con el eje E-O.
2. Excavar dos zanjas paralelas (N y S) y una transversal (E) hasta el suelo del patio.
3. El bloque aislado = envolvente del templo.
4. Tallar de arriba abajo: remate de la vimana → cuerpos → mandapa → plinto.
5. En cada cota, vaciar de fuera adentro: exteriores, luego galerías y cámaras.
6. Cerrar el frente oeste con la gopura tallada en la roca remanente.
```

La forma se define por **diferencia booleana**: `templo = bloque − vacíos`. El
modelo paramétrico la invierte: suma las primitivas retenidas y las resta de
la envolvente del patio.

## 2. Restricciones deducidas

| Restricción | Efecto en la forma |
|---|---|
| Irreversibilidad (no se puede añadir material) | Plan completo previo; márgenes de seguridad en espesores; talla descendente |
| Diaclasas y coladas del basalto | Ubicación de elementos exentos en roca sana; orientación del bloque |
| Evacuación del escombro | Secuencia de fondo (este) a frente (oeste); el frente se excava al final |
| Iluminación natural del patio | Proporción patio/profundidad; vimana como foco solar al fondo del eje |
| Tiempo (un reinado) | Ritmo ≈ 11.3 m³/día durante 18 años (KL-H3) |

## 3. Balance de materia (salida del modelo)

```
V_patio    = L · W · (d_frente + d_fondo) / 2 = 82 · 46 · 24      = 90 528 m³
V_retenido = Σ primitivas (plinto 0.85, mandapas 0.6–0.7, vimana escalonada)
           = 16 244 m³
V_extraído = 74 284 m³   →   215 423 t   (cifra citada: ~200 000 t; +7.7 %)
```

La consistencia (±8 %) no "prueba" la cifra citada, que es redonda y de
origen poco documentado; muestra que las medidas globales del patio y del
templo son coherentes con ella.

## 4. Salidas del modelo

| Archivo | Contenido |
|---|---|
| `salida/kailasa_planta.svg` | Planta: patio (vacío), plinto, mandapa, vimana escalonada, exentos |
| `salida/kailasa_volumetria.obj` | Volumen retenido (lo que no se excavó) |
| `salida/kailasa_geometria.json` | Primitivas, volúmenes con factor de macizo, balance sustractivo |

## 5. Uso como regla de diseño contemporáneo

La lógica sustractiva se traslada a proyectos excavados (arquitectura en
terreno, cimentaciones como espacio, minería urbana): diseñar el volumen
retenido como variable de proyecto y medir la eficiencia con la razón
retenido/extraído (0.22 en Kailasa).
