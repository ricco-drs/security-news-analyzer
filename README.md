# Security News Analyzer

Aplicacion en Python que recibe la URL de una noticia y muestra el titulo de
la pagina, la cantidad de palabras, la cantidad de caracteres y la fecha y
hora del analisis.

Es el proyecto del Laboratorio 1 - Construccion segura de una aplicacion
Python con pip. La aplicacion en si es simple; lo que se evalua en el
laboratorio es el manejo del arbol de dependencias que se genera al instalar
requests y beautifulsoup4.

## Integrantes

| Integrante | Usuario GitHub | Responsabilidad |
|---|---|---|
| Christopher Henrry Albino Soto | Christopher-Albino | Aplicacion, entorno virtual y requirements |
| Ricco Didier Rashuaman Sapallanay | ricco-drs | Analisis de dependencias, auditoria de seguridad e informes |

## Requisitos

- Python 3.13 o superior
- pip
- Conexion a internet (para instalar los paquetes y para que la aplicacion
  pueda descargar las paginas que se le pidan analizar)

## Instalacion

Clonar el repositorio:

```bash
git clone https://github.com/ricco-drs/security-news-analyzer.git
cd security-news-analyzer
```

Crear el entorno virtual:

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

Si PowerShell bloquea la activacion por la politica de ejecucion:
```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Verificar que el entorno quedo activo:

```bash
python --version
pip --version
```

Instalar las dependencias de la aplicacion:

```bash
pip install -r requirements.txt
```

Instalar las herramientas de analisis, solo si se van a reproducir los
reportes de pipdeptree y pip-audit:

```bash
pip install -r requirements-dev.txt
```

## Uso

```bash
python app.py
```

La aplicacion pide una URL por consola y muestra el resultado del analisis.

### Ejemplo de salida

```
=== Security News Analyzer ===
Ingrese una URL: https://www.python.org/

Resultado
----------------------------------------
Titulo: Welcome to Python.org
Caracteres: 6678
Palabras: 1119
Fecha: 2026-09-09 21:42:12
```

Si la URL no se puede acceder (dominio inexistente, timeout, error del
servidor, etc.), la aplicacion captura el error y muestra un mensaje en vez
de cerrarse de golpe.

## Pruebas realizadas

Se probo la aplicacion con tres portales de noticias peruanos y con un
dominio inexistente, para validar en un caso real las correcciones de
User-Agent, encoding y extraccion de titulo, ademas del manejo de errores.

### 1. El Comercio

```
=== Security News Analyzer ===
Ingrese una URL: https://elcomercio.pe/

Resultado
----------------------------------------
Titulo: Noticias del Perú y el Mundo de último minuto | EL COMERCIO PERÚ
Caracteres: 23233
Palabras: 3674
Fecha: 2026-09-08 18:35:36
```

### 2. RPP Noticias

```
=== Security News Analyzer ===
Ingrese una URL: https://rpp.pe/

Resultado
----------------------------------------
Titulo: Últimas Noticias del Perú y el Mundo en RPP Noticias
Caracteres: 22447
Palabras: 3591
Fecha: 2026-09-08 18:35:39
```

### 3. La República

```
=== Security News Analyzer ===
Ingrese una URL: https://larepublica.pe/

Resultado
----------------------------------------
Titulo: Últimas noticias del Perú y el Mundo | La República
Caracteres: 14497
Palabras: 2377
Fecha: 2026-09-08 18:35:42
```

### 4. Dominio inexistente (caso de error)

```
=== Security News Analyzer ===
Ingrese una URL: https://este-dominio-no-existe-laboratorio-xyz.com

No se pudo analizar la URL: HTTPSConnectionPool(host='este-dominio-no-existe-laboratorio-xyz.com', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("Failed to resolve 'este-dominio-no-existe-laboratorio-xyz.com' ([Errno 11001] getaddrinfo failed)"))
```

La aplicación captura la excepción y muestra un mensaje de error en lugar de
terminar abruptamente.

## Estructura del repositorio

```
security-news-analyzer/
├── .gitattributes           # normalizacion de saltos de linea entre SO
├── .gitignore                # excluye .venv/, __pycache__/, etc.
├── app.py                    # la aplicacion
├── requirements.txt          # dependencias de la aplicacion
├── requirements-dev.txt      # herramientas de analisis (pipdeptree, pip-audit)
├── README.md                 # este archivo
├── dependency-report.txt     # salidas crudas de las herramientas (evidencia)
└── security-report.md        # informe de analisis de dependencias y seguridad
```

### Por que hay dos archivos de requirements

`requirements.txt` tiene unicamente lo que necesita la aplicacion para
correr. `pipdeptree` y `pip-audit` son herramientas para analizar el
proyecto, no dependencias de la aplicacion, asi que se instalan aparte en
`requirements-dev.txt`. Si se mezclaran en el mismo archivo, el arbol de
dependencias que se esta estudiando en el laboratorio quedaria contaminado
con paquetes que no tienen nada que ver con la aplicacion.
