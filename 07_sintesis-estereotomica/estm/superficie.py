"""Familias de perfil y superficies de bóveda sobre planta poligonal regular.

Perfil de arco (semiluz a, apuntamiento p en [0, 1]):
    centro desplazado c = p·a, radio R = a + c,  z(x) = sqrt(R² - (x + c)²)
    p = 0 -> medio punto;  p = 1 -> apuntado equilátero (flecha √3·a).
Es el trazado con compás de los tratados: arcos de circunferencia, no
curvas escaladas.

Superficie sobre un polígono de n lados (radio circunscrito R, apotema A,
semilado s = R·sin(π/n)). En el sector de cada lado, con q = distancia
normal al lado y v = coordenada a lo largo del lado:
    arista (β = 0):  z = perfil(|v|; semiluz s)  -> cañones que se cortan en
                     aristas diagonales (crucería gótica para n = 4)
    cúpula (β = 1):  z = perfil(q; semiluz A)    -> bóveda de paños / cúpula
                     sobre tambor (nervadas califales, mocárabes)
    z = (1 - β)·z_arista + β·z_cupula
"""

import numpy as np


def centro_radio(semiluz, p):
    c = p * semiluz
    return c, semiluz + c


def z_arco(x, semiluz, p):
    """Altura del intradós a distancia x (>= 0) del eje de un arco."""
    c, R = centro_radio(semiluz, p)
    x = np.clip(np.abs(x), 0, semiluz)
    return np.sqrt(np.maximum(R ** 2 - (x + c) ** 2, 0.0))


def flecha(semiluz, p):
    return semiluz * np.sqrt(1 + 2 * p)


class SuperficiePoligonal:
    def __init__(self, n, R, apuntamiento, beta):
        self.n, self.R, self.p, self.beta = int(n), float(R), float(apuntamiento), float(beta)
        self.A = R * np.cos(np.pi / n)
        self.s = R * np.sin(np.pi / n)

    def sector(self, x, y):
        phi = np.arctan2(y, x)
        return np.mod(np.round(phi / (2 * np.pi / self.n)), self.n).astype(int)

    def locales(self, x, y):
        s = self.sector(x, y)
        ang = 2 * np.pi * s / self.n
        q = x * np.cos(ang) + y * np.sin(ang)
        v = -x * np.sin(ang) + y * np.cos(ang)
        return s, q, v

    def z(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        _, q, v = self.locales(x, y)
        zg = z_arco(v, self.s, self.p)
        zd = z_arco(np.clip(q, 0, self.A), self.A, self.p)
        return (1 - self.beta) * zg + self.beta * zd

    def gradiente(self, x, y, h=1e-4):
        h = h * self.R
        gx = (self.z(x + h, y) - self.z(x - h, y)) / (2 * h)
        gy = (self.z(x, y + h) - self.z(x, y - h)) / (2 * h)
        return gx, gy

    def normal(self, x, y):
        gx, gy = self.gradiente(x, y)
        n = np.stack([-gx, -gy, np.ones_like(np.asarray(gx, float))], axis=-1)
        return n / np.linalg.norm(n, axis=-1, keepdims=True)

    def dentro(self, x, y, tol=1e-9):
        _, q, _ = self.locales(np.asarray(x, float), np.asarray(y, float))
        return q <= self.A + tol

    def flecha(self):
        return float(self.z(0.0, 0.0))

    def vertices(self):
        ang = 2 * np.pi * np.arange(self.n) / self.n + np.pi / self.n
        return np.column_stack([self.R * np.cos(ang), self.R * np.sin(ang)])

    def normales_lado(self):
        ang = 2 * np.pi * np.arange(self.n) / self.n
        return np.column_stack([np.cos(ang), np.sin(ang)])

    def raster(self, paso):
        """Celdas de un ráster de la planta (centros dentro del polígono)."""
        g = np.arange(-self.R, self.R + paso, paso)
        X, Y = np.meshgrid(g, g)
        X, Y = X.ravel(), Y.ravel()
        m = self.dentro(X, Y)
        return X[m], Y[m]
