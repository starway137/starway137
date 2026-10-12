# Gran Estupa de Sanchi — contexto e hipótesis

## 1. Contexto

| Campo | Valor |
|---|---|
| Ubicación | Sanchi, Madhya Pradesh, India (23.4793 N, 77.7398 E), cima de colina |
| Cronología | Fundación maurya (Ashoka, s. III a.C.); ampliación y revestimiento de piedra (shunga, s. II a.C.); toranas (satavahana, s. I a.C.–I d.C.) |
| Función | Relicario budista; recorrido ritual de circunvalación (pradakshina) |
| Materiales | Núcleo de ladrillo (fase ashokana) envuelto por cascote y sillería de arenisca |
| Tipología | Estupa: anda (cúpula), medhi (terraza con deambulatorio), harmika, chhatra, vedika y cuatro toranas |

La estupa es una masa maciza sin espacio interior: su "arquitectura" es el
recorrido que genera alrededor. Es el único caso radial del dataset y el único
con simetría rotacional sin reflexión.

## 2. Preguntas de investigación

1. ¿Qué perfil geométrico define el anda y cuánto se aparta del hemisferio?
2. ¿Puede describirse el crecimiento del monumento como una homotecia?
3. ¿Cómo codifica la planta el sentido del rito?

## 3. Hipótesis

### SN-H1 — El anda es un casquete esférico truncado
- **Enunciado:** el perfil del anda corresponde a un casquete de altura menor que el radio.
- **Predicción:** H/D ≈ 0.45 (< 0.5 del hemisferio); factor de volumen (3a²+h²)/(6a²) ≈ 0.63.
- **Test:** `computos.razon_altura_diametro` en `cad_parametric/salida/sanchi_geometria.json`.
- **Falsación:** levantamiento fotogramétrico con perfil no circular (p. ej. catenario o parabólico, error RMS menor que el del círculo).

### SN-H2 — Crecimiento por encapsulamiento homotético
- **Enunciado:** la estupa shunga envuelve a la ashokana duplicando su diámetro; el volumen crece con el cubo del factor lineal.
- **Predicción:** factor de diámetro ≈ 2; factor de volumen ≈ 8.
- **Test:** `computos.test_SN_H2` y `M5_crecimiento_cronologico.sanchi_crecimiento_por_encapsulamiento`.

### SN-H3 — Simetría C4 quiral codifica la pradakshina
- **Enunciado:** los accesos acodados de la vedika forman un molinete que impone el giro horario: simetría rotacional de orden 4 sin ejes de reflexión.
- **Predicción:** grupo C4 (no D4) en planta.
- **Test:** `descriptores.json → simetria` y modelo paramétrico (retornos desplazados en sentido horario).

### SN-H4 — Proporciones del mandala circular
- **Enunciado:** la razón vedika/anda responde a un canon simple.
- **Predicción:** 44 / 36.6 = 1.20, cerca de 5:4 o de 6:5.
- **Test:** canon más próximo y probabilidad de azar en `data/features.json`; con la vedika en calidad C y una probabilidad de azar elevada, la hipótesis se considera no concluyente por diseño.

## 4. Restricciones de época deducidas

| Tipo | Restricción | Consecuencia formal |
|---|---|---|
| Material | Ladrillo y cascote + revestimiento de piedra | Masa maciza; crecimiento por capas en lugar de demolición |
| Rito | Circunvalación horaria, cuatro direcciones | Planta radial, accesos cardinales en molinete |
| Topografía | Cima de colina | Visibilidad a distancia; plataforma nivelada |
| Patronazgo | Donaciones sucesivas (inscripciones en la vedika) | Adición modular de balaustres y toranas |
