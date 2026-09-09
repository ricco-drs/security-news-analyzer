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

## 4. Plan de remediacion

### Que hay que actualizar y por que

Con los datos de `pip list --outdated`, en el entorno hay tres paquetes
desactualizados:

| Paquete | Instalada | Ultima | Es dependencia de la app? |
|---|---|---|---|
| `pip` | 25.1.1 | 26.2.1 | No, es el instalador del entorno |
| `filelock` | 3.32.5 | 3.32.6 | No, la trae `pip-audit` |
| `platformdirs` | 4.11.7 | 4.11.8 | No, la trae `pip-audit` |

Ninguna de las 7 dependencias de la aplicacion aparece desactualizada, asi
que por el lado de `requests`, `beautifulsoup4` y sus transitivas no hay
nada urgente que remediar hoy.

El unico caso que si amerita accion es `pip`. No es una dependencia de la
aplicacion, pero es la herramienta con la que se instalan todas las demas, y
tiene 7 avisos de seguridad publicados para la version 25.1.1 que trae el
entorno virtual (PYSEC-2026-196, PYSEC-2026-1795, PYSEC-2026-1796,
PYSEC-2026-2875, PYSEC-2026-2876 y PYSEC-2026-3721). Un instalador con
vulnerabilidades conocidas es un problema de cadena de suministro por si
solo: si alguien logra aprovechar un fallo en el proceso de instalacion,
puede terminar metiendo codigo en el entorno sin que ninguna de las
librerias auditadas se vea comprometida.

Remediacion propuesta:

```bash
python -m pip install --upgrade pip
```

### Que riesgo tiene actualizar

Actualizar no es gratis. Los riesgos concretos son:

- Cambios de API: una version nueva puede quitar o renombrar funciones que
  el codigo usaba. En esta aplicacion el riesgo es bajo porque solo usamos
  `requests.get()` y `BeautifulSoup(...)`, que son la parte mas estable de
  ambas librerias, pero en un proyecto grande no seria asi.
- Conflictos entre dependencias: subir un paquete puede dejar a otro sin la
  version que necesita. Por ejemplo, `requests` exige `urllib3>=1.26,<3`; si
  se instalara `urllib3` 3.x, `requests` quedaria roto.
- Cambios de comportamiento silenciosos: la funcion sigue existiendo y no
  falla, pero devuelve algo distinto. Estos son los peores porque no se ven
  hasta que algo raro pasa en produccion.

Por eso el criterio no es "actualizar todo siempre", sino actualizar lo que
tiene una razon (un aviso de seguridad, un bug que nos afecta) y verificar
despues.

### Como verificar que la actualizacion funciono

Tres comprobaciones, en este orden:

1. `pip-audit -r requirements.txt` para confirmar que la vulnerabilidad que
   motivo la actualizacion ya no aparece.
2. `pip check` para confirmar que no quedaron conflictos de versiones entre
   paquetes. En el entorno actual devuelve:

   ```
   No broken requirements found.
   ```

3. Ejecutar la aplicacion contra las URLs de prueba documentadas en el
   README (El Comercio, RPP, La Republica y el dominio inexistente) y
   comprobar que sigue devolviendo titulo, caracteres, palabras y fecha, y
   que el caso de error sigue mostrando el mensaje en vez de reventar.

El paso 3 es el que suele saltarse y es el mas importante: `pip-audit` y
`pip check` dicen que el entorno esta sano, pero no dicen si la aplicacion
sigue funcionando.

## 5. Analisis de Software Supply Chain

### El caso planteado en el laboratorio

Una aplicacion tiene 15 dependencias directas, y esas 15 requieren otras 80
librerias. La pregunta es cuantos componentes de terceros forman realmente
parte de la aplicacion.

La respuesta es 95, no 15. El equipo eligio 15 y reviso 15, pero lo que
termina ejecutandose en produccion son 95 paquetes escritos por gente que el
equipo no conoce, ninguno de los cuales pidio permiso para entrar. Y ese
numero es el minimo: cada una de las 80 puede traer las suyas propias.

### Lo mismo medido en este proyecto

No hace falta irse a un caso hipotetico, en este laboratorio pasa igual:

| | Cantidad |
|---|---|
| Paquetes que instalamos a mano | 4 (`requests`, `beautifulsoup4`, `pipdeptree`, `pip-audit`) |
| Paquetes en `requirements.txt` (la app) | 8 |
| Paquetes totales en el entorno virtual | 43 |

Por el lado de la aplicacion, 2 decisiones se convirtieron en 8 paquetes:
por cada libreria que elegimos, entraron 3 que no elegimos.

El dato mas incomodo es el otro. `pipdeptree` y `pip-audit`, las dos
herramientas que instalamos justamente para auditar la cadena de suministro,
arrastraron por si solas unos 35 paquetes mas (`rich`, `Pygments`,
`cyclonedx-python-lib`, toda la familia `nab-*`, etc.). Es decir, las
herramientas de seguridad tambien son cadena de suministro. Auditar tiene su
propio costo en superficie de ataque, y eso es exactamente lo que motiva
mantener `requirements.txt` y `requirements-dev.txt` separados: lo que se
instala para analizar no tiene por que viajar al entorno donde corre la
aplicacion.

### Quien es responsable de una vulnerabilidad en una dependencia transitiva

Esta es la pregunta de la Parte VII, y la respuesta corta es: el equipo que
mantiene la aplicacion.

Nuestro codigo no tiene ni un solo `import urllib3`. Nunca lo elegimos, no
sabemos quien lo mantiene, no leimos su codigo. Pero si mañana sale un aviso
de seguridad para la version de `urllib3` que tenemos instalada, la
aplicacion esta expuesta, porque cada `requests.get()` que hace `app.py`
termina ejecutando codigo de `urllib3`. El usuario final no distingue entre
"nuestro codigo" y "codigo que vino de arrastre": para el es una sola
aplicacion.

Quien publica el parche es el mantenedor de `urllib3`, pero quien tiene que
enterarse, evaluar si le afecta, actualizar y verificar que nada se rompio
es el equipo de la aplicacion. La responsabilidad de escribir el arreglo y
la responsabilidad de aplicarlo son cosas distintas, y la segunda no se
delega.

### Por que esto es un riesgo y que se puede hacer

Todo ese codigo de terceros se ejecuta con los mismos permisos que el
nuestro: mismo proceso, mismo acceso a disco, misma red, mismas variables de
entorno. No hay ninguna barrera entre `app.py` y la libreria numero 43 del
entorno.

Los riesgos concretos son tres:

- Vulnerabilidades, que es lo que busca `pip-audit`. Son las mas faciles de
  detectar porque estan publicadas.
- Paquetes comprometidos a proposito: una cuenta de mantenedor robada, o un
  paquete con nombre parecido a uno legitimo (`requestss` en vez de
  `requests`). Aca `pip-audit` no ayuda, porque el codigo malicioso es nuevo
  y todavia no hay aviso publicado.
- Licencias: una dependencia transitiva puede traer condiciones legales que
  nadie reviso al instalarla.

Lo que si esta a nuestro alcance en un proyecto de este tamaño:

- Fijar versiones exactas en `requirements.txt` con `==`, para que instalar
  hoy y instalar en tres meses den el mismo resultado.
- Correr `pip-audit` de forma regular y no una sola vez, porque el resultado
  cambia solo, sin que nadie toque el codigo.
- Mirar el arbol con `pipdeptree` antes de agregar una dependencia nueva:
  una libreria que resuelve algo pequeño pero arrastra veinte paquetes
  probablemente no valga la pena.
- Tener el menor numero posible de dependencias directas, que es la unica
  parte de la cadena que realmente controlamos.

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
