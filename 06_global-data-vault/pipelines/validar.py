"""Paso 1 — valida estructura, esquema e integridad referencial de los cinco casos."""

import sys

from archimorph import features, validation


def main():
    errors = validation.validate_all(features.load_materials())
    if errors:
        print("Validación FALLIDA:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("Validación OK: 5 casos, esquema e integridad referencial correctos")


if __name__ == "__main__":
    main()
