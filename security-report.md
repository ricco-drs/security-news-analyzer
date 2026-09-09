# Informe de seguridad - Security News Analyzer

Este informe analiza el arbol de dependencias de la aplicacion, generado a
partir de las dos librerias que se instalaron directamente: `requests` y
`beautifulsoup4`. Los datos vienen de `dependency-report.txt`, que contiene
la salida literal de `pip list`, `pipdeptree`, `pip list --outdated` y
`pip-audit`.

## 1. Dependencias directas

Son las que estan escritas explicitamente en `requirements.txt`, las que el
equipo instalo a proposito para construir la aplicacion:

- `requests==2.34.2`
- `beautifulsoup4==4.15.0`

## 2. Dependencias transitivas

Ninguna de estas se instalo a mano. Llegaron porque `requests` y
`beautifulsoup4` las necesitan para funcionar:

```
requests==2.34.2
├── certifi==2026.7.22
├── charset-normalizer==3.5.1
├── idna==3.19
└── urllib3==2.7.0

beautifulsoup4==4.15.0
├── soupsieve==2.9.2
└── typing_extensions==4.16.0
```

En resumen, la aplicacion depende de 2 paquetes que el equipo eligio y otros
6 que ninguno de los dos instalo directamente:

- `certifi` da la lista de autoridades certificadoras para validar HTTPS.
- `charset-normalizer` detecta la codificacion del contenido cuando el
  servidor no la declara bien (por eso `response.apparent_encoding` funciona).
- `idna` traduce dominios con caracteres no ASCII.
- `urllib3` es el cliente HTTP de bajo nivel que usa `requests` por debajo.
- `soupsieve` le da a BeautifulSoup el soporte de selectores CSS.
- `typing_extensions` son anotaciones de tipos que beautifulsoup4 usa
  internamente.

Esto es justamente lo que pide identificar el laboratorio: de los 8 paquetes
instalados en el entorno, solo 2 aparecen en el codigo con un `import`
directo. Los otros 6 estan ahi igual, ejecutandose con el mismo nivel de
confianza que si los hubieramos elegido nosotros.

## 3. Vulnerabilidades detectadas

Se ejecuto `pip-audit -r requirements.txt` el 08/09/2026, es decir, auditando
unicamente `requests`, `beautifulsoup4` y sus cinco transitivas, sin mezclar
las herramientas de analisis (`pipdeptree`, `pip-audit`) que tambien viven en
el mismo entorno virtual.

Resultado:

```
No known vulnerabilities found
```

| Paquete | Version | Vulnerabilidad | Version corregida |
|---|---|---|---|
| - | - | Ninguna encontrada | - |

Con las versiones actuales, ninguna de las 7 dependencias de la aplicacion
tiene una vulnerabilidad conocida en la base de datos que consulta pip-audit.
Esto no significa que la aplicacion sea inmune: solo dice que, a la fecha de
esta auditoria, no hay ningun CVE/PYSEC publicado para estas versiones
puntuales. Una nueva version de alguna de estas librerias podria salir
mañana con un aviso de seguridad y el resultado cambiaria sin que nosotros
tocaramos una sola linea de codigo.

Como nota aparte, correr `pip-audit` sin el flag `-r` (es decir, contra todo
el entorno virtual) si reporta 7 vulnerabilidades, pero todas pertenecen a
`pip` (el propio instalador de paquetes, que viene con el venv), no a las
dependencias de la aplicacion. Ese resultado esta documentado igual en
`dependency-report.txt` para que quede como evidencia, pero no se cuenta
aca porque `pip` no es una dependencia de Security News Analyzer, es la
herramienta con la que se instalan las dependencias.

Como la tabla de esta seccion queda vacia con el entorno real, mas abajo se
documenta una demostracion controlada con una version de `urllib3` que si
tiene vulnerabilidades conocidas, para dejar constancia de que sabemos leer
e interpretar un resultado positivo de pip-audit.

## Anexo: demostracion controlada con una version vulnerable

Esto es una prueba aparte, hecha a proposito, para ver como se ve un
resultado positivo de pip-audit. No tiene nada que ver con el entorno real
del proyecto: se hizo en un entorno virtual separado, `.venv-demo/`, que no
se sube al repositorio (esta en `.gitignore`) y que no toca ni
`requirements.txt` ni el `.venv/` de la aplicacion.

Pasos:

```bash
python -m venv .venv-demo
.venv-demo\Scripts\activate
pip install "urllib3==1.26.5" pip-audit
echo urllib3==1.26.5 > temp.txt
pip-audit -r temp.txt
```

`urllib3==1.26.5` es una version de 2021 que se sabe que tiene varios CVEs
publicados. El archivo `temp.txt` es un archivo local de un solo uso, para
poder auditar unicamente esa version sin que se mezcle con `pip-audit`
mismo (que tambien esta instalado en ese `.venv-demo` y, como se vio en la
seccion anterior, tiene su propio ruido); no se sube al repositorio ni forma
parte del entregable.

Resultado real obtenido:

```
Found 10 known vulnerabilities in 1 package
Name    Version ID              Fix Versions
------- ------- --------------- -------------
urllib3 1.26.5  PYSEC-2023-192  1.26.17,2.0.6
urllib3 1.26.5  PYSEC-2023-192  1.26.17,2.0.6
urllib3 1.26.5  PYSEC-2023-212  1.26.18,2.0.7
urllib3 1.26.5  PYSEC-2023-212  1.26.18,2.0.7
urllib3 1.26.5  PYSEC-2026-141  2.7.0
urllib3 1.26.5  PYSEC-2026-1999 2.5.0
urllib3 1.26.5  PYSEC-2026-1998 2.6.0
urllib3 1.26.5  PYSEC-2026-1995 1.26.19,2.2.2
urllib3 1.26.5  PYSEC-2026-1994 2.6.0
urllib3 1.26.5  PYSEC-2026-1996 2.6.3
```

Como se lee esta tabla: cada fila es un aviso de seguridad distinto (columna
`ID`) que afecta a la version 1.26.5 de `urllib3`, con la version minima a
la que hay que subir para dejar de estar expuesto (columna `Fix Versions`).
Los IDs repetidos (`PYSEC-2023-192` y `PYSEC-2023-212` aparecen dos veces
cada uno) son porque pip-audit consulta mas de una fuente de datos y a veces
el mismo aviso aparece registrado en ambas.

Lo importante para el laboratorio es la comparacion: en nuestro
`requirements.txt` real, `urllib3` esta en la version `2.7.0`, que ya
incluye las correcciones de todos estos avisos (la columna `Fix Versions`
de varias filas apunta justo a `2.7.0` o versiones posteriores). Por eso el
entorno real de la aplicacion no aparece en esta lista: no es que pip-audit
no funcione, es que la version que ya tenemos instalada corrige estos
problemas.
