# Gran Estupa de Sanchi — ingeniería inversa paramétrica

## 1. Regla generativa reconstruida

```
ENTRADA: eje vertical (yashti) en la cima de la colina, cuatro direcciones cardinales
1. Anda:     casquete esférico de diámetro D y flecha H = 0.45 · D
2. Medhi:    terraza perimetral a h ≈ 4.3 m con deambulatorio y baranda
3. Harmika:  cuadrado de lado ≈ 0.16 · D sobre la cima
4. Chhatra:  tres discos decrecientes sobre el yashti
5. Vedika:   anillo de diámetro ≈ 1.2 · D
6. Toranas:  4 pórticos en N, E, S, O; retorno de la vedika desplazado en sentido horario (molinete)
7. Crecimiento: D_(fase+1) = 2 · D_(fase); la fase anterior queda encapsulada
```

## 2. Restricciones deducidas

| Restricción | Efecto en la forma |
|---|---|
| Masa maciza de ladrillo y cascote | Sin espacio interior; perfil de casquete estable sin empujes |
| Reliquia inamovible en el núcleo | Crecimiento por encapsulamiento, no por sustitución |
| Rito de circunvalación | Recorridos concéntricos (suelo y medhi) y accesos en molinete |
| Donaciones sucesivas | Vedika y toranas como piezas modulares añadidas |

## 3. Salidas del modelo

| Archivo | Contenido |
|---|---|
| `salida/sanchi_planta.svg` | Planta radial con fase ashokana (trazo discontinuo), toranas y molinete |
| `salida/sanchi_volumetria.obj` | Casquete, harmika, chhatra, vedika y toranas |
| `salida/sanchi_geometria.json` | Primitivas, perfil, crecimiento y recorridos |

## 4. Uso como regla de diseño contemporáneo

- **Crecimiento por encapsulamiento:** proyectos por fases donde cada ampliación envuelve a la anterior sin demolerla (estrategia de reutilización y bajo carbono).
- **Simetría quiral:** plantas que codifican un sentido de recorrido (museos, memoriales, espacios de peregrinación).
