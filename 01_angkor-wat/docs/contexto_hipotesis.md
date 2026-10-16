# Angkor Wat — contexto e hipótesis

## 1. Contexto

| Campo | Valor |
|---|---|
| Ubicación | Siem Reap, Camboya (13.4125 N, 103.867 E), llanura aluvial al norte del Tonlé Sap |
| Cronología | c. 1113–1150, reinado de Suryavarman II |
| Función | Templo vishnuista; probable mausoleo real (orientación a poniente) |
| Materiales | Arenisca de Phnom Kulen (~40 km, transporte por canales [AW-06]); núcleo y muro exterior de laterita; terraplenes de arena |
| Tipología | Templo-montaña: representación del monte Meru (torre central), sus cuatro picos (torres de esquina), las cordilleras (galerías) y el océano cósmico (foso) |

Angkor Wat es el mayor de los templos-montaña jemeres y el único orientado
principalmente a poniente. El conjunto es un sistema territorial-hidráulico:
foso de ~190 m de anchura, recinto de laterita de 1024 × 802 m, calzada
ceremonial a lo largo del eje E-O y un núcleo de tres terrazas escalonadas que
culmina a 65 m sobre el suelo.

## 2. Preguntas de investigación

1. ¿Responde la planta a una regla generativa simple (anidamiento) o a una suma de decisiones locales?
2. ¿Qué parte de las medidas está gobernada por una métrica simbólica (hat, ciclos temporales) y qué parte por restricciones físicas?
3. ¿Cuál es la restricción física dominante: la resistencia de la piedra, la estabilidad o el terreno?

## 3. Hipótesis (formato: enunciado → predicción falsable → test)

### AW-H1 — Anidamiento con dos regímenes de escala
- **Enunciado:** la composición es una cadena de recintos rectangulares concéntricos cuyas dimensiones siguen una progresión geométrica, con un salto entre el régimen territorial (foso, recinto) y el arquitectónico (galerías, torre).
- **Predicción:** el ajuste L_k = L_0·r^k sobre toda la cadena tiene R² moderado; restringido a los niveles 2–5, R² > 0.95 y r ≈ 0.5.
- **Test:** `M3_anidamiento_exponencial` en `06_global-data-vault/modelos/modelos_escala.json`.
- **Falsación:** razones sucesivas sin tendencia (R² < 0.8 en el régimen arquitectónico).

### AW-H2 — Codificación calendárica de longitudes (Stencel et al. 1976; Mannikka 1996)
- **Enunciado:** distancias a lo largo del eje principal, medidas en hat, codifican ciclos cosmológicos (p. ej. 1728 hat ≈ Krita Yuga desde la entrada oeste hasta la torre central).
- **Predicción:** distancia borde oeste del foso → torre central ≈ 1728 hat.
- **Test:** `cad_parametric/modelo_parametrico.py` → `computos.test_AW_H2`.
- **Advertencia metodológica:** con muchos puntos medibles y muchos números "significativos", las coincidencias son probables. Un test válido exige fijar los puntos de medida antes de medir (pre-registro) y una medición independiente (LiDAR [AW-05]).

### AW-H3 — Eje equinoccial
- **Enunciado:** la orientación E-O permite que, desde la puerta oeste, el sol nazca tras la torre central en el equinoccio de primavera.
- **Predicción:** desviación del eje respecto del E-O < 1°; ángulo visual de la torre desde la puerta mayor que la altura aparente del horizonte.
- **Test:** ángulo visual en `computos.test_AW_H3`; la desviación angular queda pendiente de ortofoto (`descriptores.json → eje_principal.desviacion_deg = null`).

### AW-H4 — El terreno, no la piedra, es la restricción dominante
- **Enunciado:** la tensión media del templo-montaña sobre su huella es baja para la arenisca pero del orden de la capacidad portante de un suelo arenoso; el foso estabiliza el nivel freático y con ello la cimentación.
- **Predicción:** σ_base ≈ 0.1–0.3 MPa (capacidad típica de arenas medias) con FS ≫ 10 respecto de la piedra.
- **Test:** `M2_tension_peso_propio` (FS por elemento) + comparación con rangos geotécnicos de arenas.
- **Falsación:** σ_base ≪ 0.05 MPa (el terreno no sería restrictivo) o asientos diferenciales no correlacionados con la humedad del subsuelo.

## 4. Restricciones de época deducidas

| Tipo | Restricción | Consecuencia formal |
|---|---|---|
| Material | Arenisca en bloques sin mortero; bóveda en saledizo | Luces cortas (galerías estrechas), torres macizas escalonadas |
| Transporte | Canteras a ~40 km, transporte fluvial | Coste por bloque → modulación y reutilización de formatos |
| Terreno | Llanura arenosa con freático oscilante | Terrazas sobre relleno compactado; foso como regulador |
| Rito | Circunvalación, ascenso, orientación | Cadena de recintos + gradiente de altura hacia el centro |
