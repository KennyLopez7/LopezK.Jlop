# LopezK.J

Proyecto que contiene un juego de ajedrez jugable desde la terminal escrito en Python.

## Requisitos

- Python 3.10 o superior
- `pip` para instalar dependencias (solo `pytest` para ejecutar las pruebas)

## Instalación

Crea y activa un entorno virtual opcionalmente:

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows usa .venv\\Scripts\\activate
```

Instala las dependencias de desarrollo:

```bash
pip install -r requirements-dev.txt
```

## Uso

Para iniciar una partida interactiva:

```bash
python main.py
```

Ejemplos de comandos disponibles durante la partida:

- `e2e4`: movimiento básico
- `O-O` o `O-O-O`: enroques
- `moves e2`: lista movimientos legales desde una casilla
- `quit`: termina la partida

## Pruebas

Ejecuta `pytest` para correr la suite de pruebas automatizadas que verifican las reglas principales del juego (jaque mate, enroque, en passant y promoción).

```bash
pytest
```
