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

Como la tabla de esta seccion queda vacia con el entorno real, en el Anexo
mas abajo se documenta una demostracion controlada con una version de
`urllib3` que si tiene vulnerabilidades conocidas, para dejar constancia de
que sabemos leer e interpretar un resultado positivo de pip-audit.
