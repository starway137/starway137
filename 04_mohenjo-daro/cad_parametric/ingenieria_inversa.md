# Mohenjo-daro — ingeniería inversa por reglas

## 1. Gramática urbana reconstruida

```
R1  Retícula:   manzanas 366 × 244 m separadas por calles principales de 10 m
R2  Franjas:    cada manzana se divide en franjas E-O de 18–30 m separadas por callejones de 3 m
R3  Lotes:      cada franja se divide en lotes de 12–26 m (E-O)
R4  Módulo:     toda medida se ajusta a n · (0.28 + 0.01) m (ladrillo + junta)
R5  Casa-patio: patio central ≈ 30 % del lote; muros perimetrales
R6  Ciudadela:  plataforma de adobe 200 × 400 × 12 m, separada ~200 m al oeste
R7  Gran Baño:  estanque 7.01 × 11.88 × 2.43 m en un edificio de 33 × 55 m sobre la ciudadela
```

Las reglas R2–R3 introducen variación aleatoria acotada (semilla fija = 7) para
representar el crecimiento orgánico dentro de una norma: la ciudad es un
**sistema paramétrico estocástico**, no un trazado único.

## 2. Restricciones deducidas

| Restricción | Efecto en la forma |
|---|---|
| Ladrillo estandarizado | Medidas discretas; aparejos repetibles; norma regional |
| Crecidas del Indo | Plataformas elevadas; drenaje cubierto en las calles |
| Calor | Casas introvertidas, pocos vanos a la calle, patios |
| Agua doméstica | Pozos en lotes y drenaje conectado a la red viaria |

## 3. Salidas del modelo

| Archivo | Contenido |
|---|---|
| `salida/mohenjo_daro_planta.svg` | Ciudadela, Gran Baño y 6 manzanas con 1009 casas-patio |
| `salida/mohenjo_daro_volumetria.obj` | Volumetría (casas como prismas de 6 m) |
| `salida/mohenjo_daro_geometria.json` | Primitivas y densidades (test MD-H3) |

## 4. Advertencia de circularidad

El generador impone el módulo del ladrillo (R4); por eso no puede probar MD-H2.
Sirve para explorar consecuencias (densidad, número de casas, tamaño de lote)
y como prior generativo de tejidos urbanos modulares. La prueba de MD-H2
requiere medidas independientes.
