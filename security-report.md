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

## 6. Parte VIII: comparacion antes y despues de actualizar

Lo primero fue ver que habia desactualizado en el entorno:

```
$ pip list --outdated
Package      Version Latest Type
------------ ------- ------ -----
filelock     3.32.5  3.32.6 wheel
pip          25.1.1  26.2.1 wheel
platformdirs 4.11.7  4.11.8 wheel
```

Ninguna dependencia de la aplicacion aparece en esa lista. Aun asi corrimos
el comando que pide la guia:

```
$ pip install --upgrade requests
Requirement already satisfied: requests in .venv\lib\site-packages (2.34.2)
Requirement already satisfied: charset_normalizer<4,>=2 ... (3.5.1)
Requirement already satisfied: idna<4,>=2.5 ... (3.19)
Requirement already satisfied: urllib3<3,>=1.26 ... (2.7.0)
Requirement already satisfied: certifi>=2023.5.7 ... (2026.7.22)
```

`requests` ya estaba en la ultima version, asi que el comando no hizo nada.
Esto ya deja algo: ejecutar el comando de actualizar no significa que haya
algo para actualizar. Si nos quedabamos ahi, el ejercicio terminaba sin
ningun cambio que comparar.

El paquete que si tenia una razon concreta para actualizarse era `pip`, por
las 7 vulnerabilidades que salieron en la seccion 3. Asi que hicimos esa
actualizacion, que ademas es la que nosotros mismos propusimos en el plan de
remediacion:

```
$ python -m pip install --upgrade pip
  Attempting uninstall: pip
    Found existing installation: pip 25.1.1
    Uninstalling pip-25.1.1:
      Successfully uninstalled pip-25.1.1
Successfully installed pip-26.2.1
```

### ANTES

- Dependencias: 43 paquetes en el entorno, 8 de la aplicacion.
- Vulnerabilidades: 7 avisos, todos en `pip 25.1.1`. Las dependencias de la
  aplicacion, limpias.
- Versiones: `pip 25.1.1`, `requests 2.34.2`, `urllib3 2.7.0`,
  `beautifulsoup4 4.15.0`.

### DESPUES

- Dependencias: 43 paquetes. La cantidad no cambio, actualizar `pip` no
  agrego ni quito nada del arbol.
- Vulnerabilidades: ninguna. `pip-audit` sobre todo el entorno ahora
  devuelve `No known vulnerabilities found`, no solo sobre
  `requirements.txt`.
- Versiones: `pip 26.2.1`. Todo lo demas quedo igual.

La unica linea que cambio en toda la comparacion es la version de `pip`, y
con eso desaparecieron las 7 vulnerabilidades. Es el mejor caso posible de
una actualizacion: arregla lo que tenia que arreglar y no toca nada mas.

### Habia que regenerar requirements.txt?

La guia dice que despues de actualizar hay que correr
`pip freeze > requirements.txt`. Nosotros no lo hicimos a ciegas, por dos
motivos.

El primero es que en este entorno estan instaladas tambien `pipdeptree` y
`pip-audit`, asi que un `pip freeze` habria escrito los 43 paquetes dentro
del `requirements.txt` de la aplicacion, que es justo el problema que
veniamos evitando con los dos archivos separados.

El segundo es que no hacia falta. Comparamos las versiones instaladas de las
8 dependencias de la aplicacion contra lo que ya decia el archivo y son
identicas, no hay una sola diferencia. `pip` no aparece en `requirements.txt`
(pip freeze no lo incluye nunca, es parte del entorno virtual, no una
dependencia del proyecto), asi que actualizarlo no cambia el archivo.

Conclusion: `requirements.txt` se quedo como estaba, y eso es correcto, no
un olvido.

### La aplicacion sigue funcionando?

Esta es la verificacion que importa, y la hicimos con las mismas cuatro URLs
del README:

| URL | Resultado |
|---|---|
| elcomercio.pe | Titulo, 23100 caracteres, 3672 palabras |
| rpp.pe | Titulo, 22380 caracteres, 3581 palabras |
| larepublica.pe | Titulo, 14497 caracteres, 2377 palabras |
| dominio inexistente | Mensaje de error controlado, no se cae |

Los numeros de caracteres y palabras no dan exactamente igual que en las
pruebas del README, pero eso no es culpa de la actualizacion: son portales
de noticias y cambian el contenido de la portada cada pocos minutos. Los
titulos, los acentos y el manejo del error siguen igual, que es lo que
teniamos que comprobar.

Ademas:

```
$ pip check
No broken requirements found.
```

### Actualizar siempre soluciona el problema?

No. En este caso salio bien, pero eso fue suerte del tamaño del proyecto.
Actualizar un paquete puede romper la aplicacion si la version nueva cambia
la API, puede pelearse con otra dependencia que necesitaba la version vieja,
o puede cambiar un comportamiento sin avisar y que el error aparezca mucho
despues. Por eso la parte de verificar no es opcional: sin correr la
aplicacion despues, lo unico que sabemos es que el auditor esta contento.

## 7. Preguntas de reflexion

### 1. Cual es la diferencia entre dependencia directa y transitiva

La directa es la que pedimos nosotros, a proposito. La transitiva llega
porque otra la necesita.

En este proyecto escribimos `pip install requests beautifulsoup4` y esas dos
son las directas. Las otras seis (`certifi`, `charset-normalizer`, `idna`,
`urllib3`, `soupsieve`, `typing_extensions`) nunca las escribimos en ningun
lado, aparecieron solas. La diferencia no esta en el codigo, esta en quien
tomo la decision: dos las decidimos nosotros y seis las decidieron los
autores de `requests` y `beautifulsoup4` por nosotros.

### 2. Por que pip freeze puede mostrar mas paquetes de los que aparecen en nuestro codigo

Porque `pip freeze` lee el entorno virtual, no el codigo. No le importa si
el paquete tiene un `import` en `app.py` o si nunca se usa, lo lista igual
mientras este instalado.

Nuestro `app.py` tiene tres imports (`requests`, `bs4` y `datetime`, y este
ultimo es de la libreria estandar). El `requirements.txt` tiene ocho lineas.
Y si corriamos `pip freeze` en el entorno donde estan las herramientas de
analisis, salian 43. Los tres numeros son correctos, solo estan midiendo
cosas distintas: lo que el codigo usa, lo que la aplicacion necesita
instalado, y lo que hay en el entorno.

### 3. Una aplicacion puede tener una vulnerabilidad aunque nuestro codigo no tenga ningun import de la libreria vulnerable

Si, y `urllib3` es el ejemplo perfecto en este proyecto.

En `app.py` no aparece la palabra `urllib3` por ningun lado. Pero cada vez
que se ejecuta `requests.get(url, headers=HEADERS, timeout=10)`, quien abre
la conexion, negocia el TLS y maneja los reintentos es `urllib3`. Si tiene
un fallo, nuestra aplicacion lo tiene, aunque nosotros no lo hayamos
importado ni sepamos que existe.

En el anexo se ve concretamente: la version 1.26.5 de `urllib3` arrastra 10
avisos de seguridad. Si nuestro entorno tuviera esa version en vez de la
2.7.0, la aplicacion estaria expuesta sin que cambiara una sola linea de
`app.py`.

### 4. Actualizar todas las dependencias automaticamente es una buena estrategia

No. Es tentador porque suena a estar siempre al dia, pero es tratar todos
los cambios como si fueran iguales.

En la Parte VIII se vio de los dos lados. Actualizar `pip` tenia una razon
concreta (7 vulnerabilidades) y salio perfecto: desaparecieron los avisos y
no se rompio nada. Actualizar `requests` no tenia ninguna razon, y el
comando directamente no hizo nada porque ya estaba en la ultima version.
Actualizar por actualizar habria sido puro ruido.

El problema de automatizarlo todo es que una version nueva puede cambiar la
API, puede chocar con otra dependencia que necesitaba la vieja, o puede
cambiar un comportamiento sin avisar. Nuestro caso es chico y `requests.get`
es de lo mas estable que hay, pero en un proyecto grande actualizar 40
paquetes de golpe y que algo falle deja el problema de averiguar cual de los
40 fue.

Lo razonable es actualizar lo que tiene un motivo, y verificar despues.

### 5. Por que las dependencias representan un riesgo para la Software Supply Chain

Porque terminamos ejecutando muchisimo mas codigo ajeno del que revisamos, y
ese codigo corre con los mismos permisos que el nuestro.

El numero de este proyecto lo dice bastante claro: instalamos cuatro cosas a
mano y el entorno quedo con 43 paquetes. Nadie del equipo leyo el codigo de
esos 43, no sabemos quien los mantiene, y sin embargo cualquiera de ellos
puede leer archivos, abrir conexiones o acceder a las variables de entorno
igual que `app.py`.

El riesgo tiene tres formas. La vulnerabilidad publicada, que es la mas
manejable porque `pip-audit` la encuentra. El paquete comprometido a
proposito, ya sea por una cuenta de mantenedor robada o por un nombre
parecido al de uno legitimo, que es peor porque todavia no hay aviso que
consultar. Y la licencia, que no rompe nada tecnicamente pero puede traer
condiciones legales que nadie miro.

Lo unico que controlamos de verdad es la lista de dependencias directas.
Todo lo que viene detras lo heredamos.

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
