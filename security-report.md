# Informe de seguridad - Security News Analyzer

Este informe es el analisis de las dependencias de la aplicacion. Los datos
salen todos de `dependency-report.txt`, que tiene la salida tal cual de
`pip list`, `pipdeptree`, `pip list --outdated` y `pip-audit`. Aca lo que
hacemos es explicar que significa eso.

## 1. Dependencias directas

Las que pusimos nosotros en `requirements.txt` a proposito:

- `requests==2.34.2`
- `beautifulsoup4==4.15.0`

Y ya, son solo esas dos.

## 2. Dependencias transitivas

Estas no las instalamos nosotros. Vienen porque `requests` y
`beautifulsoup4` las necesitan para poder funcionar:

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

O sea, de los 8 paquetes que terminan en el `requirements.txt`, solo 2 los
elegimos a proposito. Los otros 6 los trajo pip solo. Rapido, para que
quede claro para que sirve cada uno:

`certifi` trae la lista de autoridades certificadoras para que las
conexiones HTTPS se puedan validar. `charset-normalizer` es el que detecta
la codificacion cuando el servidor no la manda bien en la cabecera (por eso
funciona lo de `response.apparent_encoding` en `app.py`). `idna` sirve para
traducir dominios que tienen caracteres no ASCII. `urllib3` es el que en
realidad abre la conexion HTTP, `requests` es como una capa mas facil de
usar encima de el. `soupsieve` le da a BeautifulSoup los selectores tipo
CSS. Y `typing_extensions` son anotaciones de tipos que usa beautifulsoup4
por dentro, nosotros nunca las tocamos.

Ese es justo el punto que quiere que veamos el laboratorio: nuestro codigo
solo tiene un `import requests` y un `import beautifulsoup4`, pero el
entorno esta corriendo 8 paquetes, no 2.

## 3. Vulnerabilidades detectadas

Corrimos `pip-audit -r requirements.txt`, o sea auditando solo las 8
dependencias de la aplicacion (las 2 directas y sus 6 transitivas), sin
meter en la mezcla las herramientas de analisis que tambien tenemos
instaladas en el mismo entorno.

Resultado:

```
No known vulnerabilities found
```

| Paquete | Version | Vulnerabilidad | Version corregida |
|---|---|---|---|
| - | - | Ninguna encontrada | - |

Osea que ninguna de las 8 tiene, hoy, un CVE o PYSEC publicado para la
version que tenemos instalada. Eso no quiere decir que sean invulnerables
para siempre, solo que a la fecha de esta auditoria no hay nada reportado.
Puede salir un aviso mañana mismo sin que nosotros cambiemos nada.

Ahora, algo que nos parecio importante dejar anotado: si en vez de
`-r requirements.txt` corremos `pip-audit` a secas (sobre todo el entorno
virtual), en ese momento si salian 7 avisos, pero todos eran de `pip`, el
instalador de paquetes. Ese resultado tambien esta guardado en
`dependency-report.txt` como evidencia, pero no lo contamos en la tabla de
arriba porque `pip` no es una dependencia de la aplicacion, es la
herramienta con la que se instalan las dependencias. Mas adelante, en la
seccion 6, mostramos que paso con eso despues de actualizarlo.

Y como la tabla de vulnerabilidades nos quedo vacia (que en realidad es
buena noticia, pero mala para el ejercicio de "leer una tabla llena"), mas
abajo hicimos aparte una prueba con una version vieja de `urllib3` que si
tiene vulnerabilidades, para demostrar que sabemos interpretar un resultado
cuando si aparece algo.

## 4. Plan de remediacion

### Que actualizar y por que

`pip list --outdated` marco tres paquetes desactualizados en el entorno:

| Paquete | Instalada | Ultima | Es de la aplicacion? |
|---|---|---|---|
| `pip` | 25.1.1 | 26.2.1 | No, es el instalador |
| `filelock` | 3.32.5 | 3.32.6 | No, la trae `pip-audit` |
| `platformdirs` | 4.11.7 | 4.11.8 | No, la trae `pip-audit` |

Ninguna de las 8 dependencias de la app aparece ahi, asi que de ese lado no
hay nada urgente.

El que si necesitaba actualizarse era `pip`. Tenia 7 avisos de seguridad
publicados para la 25.1.1 (en realidad son 6 avisos distintos:
PYSEC-2026-196, PYSEC-2026-1795, PYSEC-2026-1796, PYSEC-2026-2875,
PYSEC-2026-2876 y PYSEC-2026-3721, pero pip-audit lista PYSEC-2026-196 dos
veces porque le llega de dos fuentes distintas, asi que en la tabla salen
7 filas). Aunque no es una dependencia nuestra, es la herramienta con la
que se instala todo lo demas, y un instalador con fallas conocidas ya es
un problema de cadena de suministro por si solo.

Lo que hicimos:

```bash
python -m pip install --upgrade pip
```

### Riesgo de actualizar

No es gratis actualizar asi nomas. Puede pasar que:

- Cambie la API y una funcion que usabamos ya no exista o se llame
  distinto. Aca el riesgo es bajo porque en `app.py` solo usamos
  `requests.get()` y `BeautifulSoup(...)`, que son de lo mas estable que
  tienen esas librerias, pero en un proyecto mas grande esto pesa mas.
- Se genere un conflicto con otra dependencia. Por ejemplo `requests` pide
  `urllib3>=1.26,<3`, entonces si alguien instalara `urllib3` en su version
  3, `requests` se rompe.
- Cambie el comportamiento sin que nadie se de cuenta al toque, que es lo
  peor porque el error puede aparecer recien despues, en produccion.

Por eso no se trata de actualizar todo siempre, sino de actualizar lo que
tiene un motivo real (un aviso de seguridad, un bug que nos afecta a
nosotros) y despues verificar que nada se rompio.

### Como verificamos que funciono

Hicimos tres cosas:

1. Volver a correr `pip-audit -r requirements.txt` para confirmar que ya no
   sale la vulnerabilidad.
2. `pip check`, que nos dice si quedo algun conflicto de versiones entre
   paquetes. Devolvio:

   ```
   No broken requirements found.
   ```

3. Correr la aplicacion contra las mismas URLs de prueba del README (El
   Comercio, RPP, La Republica y el dominio que no existe) para ver que
   siga devolviendo titulo, caracteres, palabras y fecha bien, y que el
   error siga mostrandose controlado.

El paso 3 es el que mas facil se salta, y para nosotros es el mas
importante: que `pip-audit` y `pip check` digan que todo esta bien no
significa que la aplicacion siga corriendo.

## 5. Analisis de Software Supply Chain

### El caso del laboratorio

Una app tiene 15 dependencias directas, y esas 15 arrastran otras 80
librerias mas. La pregunta es cuantos componentes de terceros forman parte
realmente de esa aplicacion.

La respuesta es 95, no 15. Uno elige y revisa 15, pero en produccion
terminan corriendo 95 paquetes que escribio gente que uno ni conoce. Y ese
95 es el piso, porque cada una de esas 80 puede traer las suyas propias
tambien.

### Lo mismo pero con nuestro proyecto

No hace falta pensarlo en abstracto, a nosotros nos paso lo mismo a
escala chica:

| | Cantidad |
|---|---|
| Paquetes instalados a mano | 4 (`requests`, `beautifulsoup4`, `pipdeptree`, `pip-audit`) |
| Paquetes en `requirements.txt` (solo la app) | 8 |
| Paquetes totales en el entorno virtual | 43 |

De la aplicacion en si: elegimos 2 librerias y terminamos con 8 en total,
osea que por cada una que elegimos entraron 3 que no.

Pero el dato que mas nos llamo la atencion fue el otro. `pipdeptree` y
`pip-audit`, que son las herramientas que instalamos justamente para
auditar la cadena de suministro, trajeron solas como 35 paquetes mas
(`rich`, `Pygments`, `cyclonedx-python-lib`, toda la familia de `nab-*`,
etc). O sea que las herramientas de seguridad tambien son parte de la
cadena de suministro, tienen su propio riesgo. Y esto es justo el motivo
por el que separamos `requirements.txt` de `requirements-dev.txt`: lo que
se instala solo para analizar no deberia mezclarse con lo que corre la
aplicacion de verdad.

### Quien responde por una vulnerabilidad en una transitiva

Esta pregunta la hace el laboratorio en la Parte VII y la respuesta es: el
equipo que mantiene la aplicacion, aunque no la haya elegido.

En `app.py` no hay ni un `import urllib3`. Nadie del equipo la eligio, no
sabemos ni quien la mantiene. Pero si mañana le sale un aviso de seguridad
a la version que tenemos instalada, nuestra app queda expuesta igual,
porque cada vez que se llama `requests.get()` por debajo se esta corriendo
codigo de `urllib3`. Al usuario final no le importa si el fallo vino de
"nuestro" codigo o de algo que arrastramos, para el es una sola cosa que
no funciona.

El que arregla el bug es el mantenedor de `urllib3`, pero enterarse de que
existe, ver si nos afecta, actualizar y confirmar que no se rompio nada, es
trabajo nuestro. Eso no se le puede pasar a nadie mas.

### Por que es un riesgo y que podemos hacer

Todo ese codigo de terceros corre con los mismos permisos que el nuestro,
mismo proceso, mismo acceso a disco y a la red. No hay ninguna pared entre
`app.py` y el paquete numero 43 del entorno.

Los riesgos son basicamente tres. Uno, que tenga una vulnerabilidad
publicada, que es el mas facil de agarrar porque `pip-audit` lo encuentra.
Dos, que sea un paquete comprometido a proposito (le robaron la cuenta al
mantenedor, o alguien subio uno con un nombre parecido, tipo `requestss` en
vez de `requests`) y ahi `pip-audit` no ayuda porque todavia no hay ningun
aviso de eso. Y tres, temas de licencia, que no rompe nada tecnicamente
pero puede meter condiciones legales que nadie reviso.

Lo que si podemos hacer en un proyecto de este tamaño: fijar versiones
exactas con `==` para que instalar hoy o en tres meses de exactamente lo
mismo, correr `pip-audit` seguido y no solo una vez (porque el resultado
cambia solo, sin que nadie toque codigo), mirar el arbol con `pipdeptree`
antes de meter una libreria nueva (si resuelve algo chiquito pero arrastra
veinte paquetes, capaz no vale la pena), y tratar de tener pocas
dependencias directas, porque es lo unico que realmente controlamos.

## 6. Parte VIII: comparacion antes y despues de actualizar

Primero vimos que estaba desactualizado:

```
$ pip list --outdated
Package      Version Latest Type
------------ ------- ------ -----
filelock     3.32.5  3.32.6 wheel
pip          25.1.1  26.2.1 wheel
platformdirs 4.11.7  4.11.8 wheel
```

Ninguna dependencia de la app sale ahi. Igual corrimos el comando que pide
la guia:

```
$ pip install --upgrade requests
Requirement already satisfied: requests in .venv\lib\site-packages (2.34.2)
Requirement already satisfied: charset_normalizer<4,>=2 ... (3.5.1)
Requirement already satisfied: idna<4,>=2.5 ... (3.19)
Requirement already satisfied: urllib3<3,>=1.26 ... (2.7.0)
Requirement already satisfied: certifi>=2023.5.7 ... (2026.7.22)
```

`requests` ya estaba en su ultima version, entonces no hizo nada. Eso
tambien es una respuesta valida: correr el comando de actualizar no
significa que haya algo que actualizar.

Lo que si tenia sentido actualizar era `pip`, por las 7 vulnerabilidades
de la seccion 3 (y porque nosotros mismos lo propusimos en el plan de
remediacion):

```
$ python -m pip install --upgrade pip
  Attempting uninstall: pip
    Found existing installation: pip 25.1.1
    Uninstalling pip-25.1.1:
      Successfully uninstalled pip-25.1.1
Successfully installed pip-26.2.1
```

### Antes

- 43 paquetes en el entorno, 8 de la aplicacion.
- 7 avisos de seguridad, todos en `pip 25.1.1`. Las dependencias de la app,
  limpias.
- `pip 25.1.1`, `requests 2.34.2`, `urllib3 2.7.0`, `beautifulsoup4 4.15.0`.

### Despues

- Siguen siendo 43 paquetes, actualizar `pip` no agrega ni quita nada del
  arbol.
- `pip-audit` sobre todo el entorno ahora dice `No known vulnerabilities
  found`, ya no solo sobre `requirements.txt`.
- `pip 26.2.1`. Todo lo demas quedo tal cual.

En resumen lo unico que cambio fue la version de pip, y con eso solo ya se
fueron las 7 vulnerabilidades. Nos parece el mejor escenario que nos podia
tocar: arreglo lo que tenia que arreglar y no rompio nada al lado.

### Y el requirements.txt, habia que regenerarlo?

La guia dice que despues de actualizar toca correr
`pip freeze > requirements.txt`. Nosotros lo pensamos dos veces antes de
hacerlo asi nomas.

Primero porque en este mismo entorno tambien tenemos instaladas
`pipdeptree` y `pip-audit`, entonces un `pip freeze` iba a meter los 43
paquetes dentro del `requirements.txt` de la app, que es justo lo que
veniamos evitando desde que separamos los dos archivos.

Y segundo porque no hacia falta: comparamos las 8 versiones instaladas
contra lo que ya decia el archivo y son exactamente las mismas. `pip` ni
siquiera aparece ahi (pip freeze nunca lo mete, es del entorno virtual, no
una dependencia del proyecto), asi que actualizarlo no cambia nada del
archivo.

O sea que `requirements.txt` se quedo igual, y eso fue a proposito, no que
se nos olvido hacerlo.

### La app sigue funcionando?

Aca esta la parte que de verdad importa. Probamos con las mismas cuatro
URLs del README:

| URL | Resultado |
|---|---|
| elcomercio.pe | Titulo bien, 23100 caracteres, 3672 palabras |
| rpp.pe | Titulo bien, 22380 caracteres, 3581 palabras |
| larepublica.pe | Titulo bien, 14497 caracteres, 2377 palabras |
| dominio inexistente | Mensaje de error controlado, no se cae |

Los numeros de caracteres y palabras no son identicos a los del README,
pero eso es porque son portales de noticias y la portada cambia cada rato,
no por la actualizacion. Lo que si sigue igual son los titulos con acentos
bien y el manejo del error, que era lo que teniamos que comprobar.

Tambien corrimos:

```
$ pip check
No broken requirements found.
```

### Actualizar siempre soluciona el problema?

No. A nosotros nos salio bien esta vez, pero fue porque el proyecto es
chico. Actualizar un paquete puede romper la app si cambia la API, puede
chocar con otra dependencia que necesitaba la version vieja, o puede
cambiar algo en silencio y que el error salga recien mas adelante. Por eso
el paso de verificar no es opcional: si no corres la app despues, lo unico
que sabes es que la herramienta de auditoria quedo contenta, no que tu
proyecto siga andando.

## 7. Preguntas de reflexion

### 1. Cual es la diferencia entre dependencia directa y transitiva

La directa la pedimos nosotros a proposito, la transitiva llega porque otra
la necesita para funcionar.

Nosotros escribimos `pip install requests beautifulsoup4`, esas dos son las
directas. Las otras seis (`certifi`, `charset-normalizer`, `idna`,
`urllib3`, `soupsieve`, `typing_extensions`) nunca las escribimos en ningun
lado, aparecieron solas cuando pip resolvio lo que requests y beautifulsoup4
necesitaban. La diferencia no esta en el codigo, esta en quien tomo la
decision de instalarla.

### 2. Por que pip freeze puede mostrar mas paquetes de los que aparecen en nuestro codigo

Porque `pip freeze` lee lo que hay instalado en el entorno, no lee
`app.py`. No le importa si algo tiene un `import` o no, si esta instalado
lo lista.

Nuestro `app.py` tiene tres imports (`requests`, `bs4` y `datetime`, este
ultimo de la libreria estandar de python). El `requirements.txt` tiene
ocho lineas. Y si hacemos `pip freeze` en el entorno donde tambien estan
las herramientas de analisis, salen 43. Los tres numeros estan bien, cada
uno mide algo distinto: lo que el codigo usa, lo que la app necesita
instalado, y lo que hay realmente en el entorno.

### 3. Una aplicacion puede tener una vulnerabilidad aunque nuestro codigo no tenga ningun import de la libreria vulnerable

Si, y en este proyecto `urllib3` es justo el ejemplo.

En `app.py` no aparece la palabra `urllib3` en ningun lado. Pero cada vez
que corre `requests.get(url, headers=HEADERS, timeout=10)`, la que
realmente abre la conexion, negocia el TLS y maneja los reintentos es
`urllib3`. Si tuviera un fallo, nuestra app lo tendria igual, aunque
nosotros nunca la hayamos importado ni supieramos que existia.

En el anexo se ve bien concreto: la version 1.26.5 de `urllib3` tiene 10
avisos de seguridad. Si nuestro entorno tuviera esa version en vez de la
2.7.0, estariamos expuestos sin haber tocado una sola linea de `app.py`.

### 4. Actualizar todas las dependencias automaticamente es una buena estrategia

No. Suena bien porque uno cree que asi esta siempre al dia, pero es tratar
cualquier actualizacion como si todas fueran iguales.

En la Parte VIII nos toco ver los dos casos. Actualizar `pip` tenia una
razon de peso (7 vulnerabilidades) y salio perfecto, se fueron los avisos
y no se rompio nada. Actualizar `requests` no tenia ninguna razon, y de
hecho el comando no hizo nada porque ya estaba en su ultima version.
Actualizar sin motivo hubiera sido solo ruido.

El problema de hacerlo todo automatico es que una version nueva te puede
cambiar la API, chocar con otra dependencia que necesitaba la version
anterior, o cambiar algo en silencio. Nuestro caso es chico y
`requests.get` es de lo mas estable que existe, pero en un proyecto grande,
actualizar 40 paquetes de una y que algo falle te deja el problema de
averiguar cual de los 40 fue.

Lo que si tiene sentido es actualizar lo que tiene un motivo, y verificar
despues.

### 5. Por que las dependencias representan un riesgo para la Software Supply Chain

Porque terminamos corriendo muchisimo mas codigo ajeno del que en
realidad revisamos, y ese codigo tiene los mismos permisos que el nuestro.

El numero de este proyecto lo deja bastante claro: instalamos 4 cosas a
mano y el entorno termino con 43 paquetes. Nadie del equipo leyo el codigo
de esos 43, no sabemos quien los mantiene, y aun asi cualquiera de ellos
puede leer archivos, abrir conexiones o leer variables de entorno igual que
`app.py`.

El riesgo se puede dar de tres formas distintas: una vulnerabilidad
publicada (la mas facil de encontrar, para eso sirve `pip-audit`), un
paquete comprometido a proposito (cuenta de mantenedor robada, o un nombre
parecido a uno legitimo, y ahi `pip-audit` no sirve porque todavia no hay
aviso), o un tema de licencias que puede traer condiciones legales que
nadie reviso.

Lo unico que en verdad controlamos es la lista de dependencias directas.
Todo lo demas lo heredamos.

## 8. Actividad grupal: detective de dependencias

El caso: una app tiene una alerta de seguridad, y el desarrollador dice
que ninguna de las librerias que el instalo directamente tiene
vulnerabilidades. Hay que investigar si con eso alcanza para decir que la
app es segura.

Nos dimos cuenta que nuestro propio proyecto es justo ese caso. Cuando
corrimos `pip-audit -r requirements.txt` salio `No known vulnerabilities
found`, asi que nosotros podriamos decir la misma frase que el
desarrollador del enunciado sin estar mintiendo. Aun asi fuimos revisando
punto por punto.

### Dependencias directas

Dos: `requests==2.34.2` y `beautifulsoup4==4.15.0`. Las unicas que alguien
del equipo eligio.

### Dependencias transitivas

Seis: `certifi`, `charset-normalizer`, `idna`, `urllib3`, `soupsieve` y
`typing_extensions`. Aca ya se ve el primer problema con lo que dice el
desarrollador: de los 8 paquetes que necesita la app, el solo habla de 2.
Se le esta quedando fuera el 75% del arbol.

### Versiones instaladas

Todas fijadas con `==`, ninguna con rango abierto. Eso al menos asegura
que instalar hoy o en tres meses da lo mismo, que es el minimo para que
una auditoria sirva de algo.

### Vulnerabilidades

Sobre las 8 dependencias de la app, cero. Sobre el entorno completo, 7
avisos, todos en `pip`. Y este es el punto que tumba el argumento del
desarrollador: `pip` no es algo que el instalo, viene con el entorno
virtual, entonces su frase sigue siendo verdad al pie de la letra y aun
asi habia 7 vulnerabilidades adentro.

### Dependencias que necesitan actualizarse

`pip list --outdated` marcaba tres: `pip`, `filelock` y `platformdirs`.
Ninguna de la aplicacion. `pip` ya lo actualizamos en la Parte VIII.
`filelock` y `platformdirs` estan una version parche atras, sin ningun
aviso asociado, se pueden dejar tranquilos.

### Posibles conflictos

`pip check` dice `No broken requirements found`, hoy no hay ninguno. Pero
mirando el arbol se ve donde podria salir uno mas adelante: `requests`
pide `urllib3>=1.26,<3` y nosotros tenemos la 2.7.0. Si algun dia hubiera
que subir a `urllib3` en su version 3 por algun aviso de seguridad,
`requests` todavia no lo aceptaria, y ahi si tendriamos un conflicto real
que resolver.

### Riesgos para la aplicacion

El riesgo hoy no es ninguna vulnerabilidad concreta, porque no hay. El
riesgo es que el equipo cree que esta mirando 2 paquetes cuando en
realidad depende de 8, y que el entorno donde corre todo tiene 43. Lo que
no se mira, no se actualiza.

### Conclusion

La afirmacion del desarrollador no alcanza. Solo cubre las dependencias
directas, que son la minoria (en nuestro caso 2 de 8), y el codigo de
`urllib3` corre en cada peticion aunque nadie lo haya elegido ni escrito
un `import`. Tampoco cubre todo lo que hay instalado, como paso con `pip`,
que ni siquiera es una dependencia declarada en ningun archivo y tenia 7
avisos publicados. Y encima esta en presente: un `pip-audit` limpio dice
que hoy no hay nada, no que mañana tampoco vaya a haber. El resultado
puede cambiar de un dia para otro sin que nadie toque una linea de codigo.

Para saber de verdad si una app es segura habria que auditar el arbol
completo, no solo lo que se instalo a mano, y hacerlo seguido, no una vez
y listo.

## Anexo: demostracion controlada con una version vulnerable

Esta prueba la hicimos aparte, a proposito, solo para ver como se ve un
resultado positivo de pip-audit. No tiene nada que ver con el entorno real
del proyecto: la hicimos en un venv separado, `.venv-demo/`, que no se
sube al repositorio (esta en el `.gitignore`) y que no toca ni el
`requirements.txt` ni el `.venv/` de la aplicacion.

Pasos:

```bash
python -m venv .venv-demo
.venv-demo\Scripts\activate
pip install "urllib3==1.26.5" pip-audit
echo urllib3==1.26.5 > temp.txt
pip-audit -r temp.txt
```

`urllib3==1.26.5` es una version de 2021 con varios CVE publicados. El
`temp.txt` es un archivo local de un solo uso, para poder auditar
unicamente esa version sin que se mezcle con `pip-audit` mismo (que
tambien vive en ese `.venv-demo` y, como vimos en la seccion 3, mete su
propio ruido). No se sube al repositorio ni es parte del entregable.

Resultado que nos salio:

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

Cada fila es un aviso distinto (columna `ID`) para la version 1.26.5, y la
columna `Fix Versions` dice a que version hay que subir para dejar de
estar expuesto. Los IDs que se repiten (`PYSEC-2023-192` y
`PYSEC-2023-212` salen dos veces cada uno) es porque pip-audit consulta
mas de una base de datos y a veces el mismo aviso aparece registrado en
ambas.

Lo que nos importa comparar es esto: en nuestro `requirements.txt` real,
`urllib3` esta en la 2.7.0, que ya trae las correcciones de todos estos
avisos (varias filas de `Fix Versions` apuntan justo a `2.7.0` o mas
arriba). Por eso nuestro entorno no aparece en esta lista, no porque
pip-audit no funcione, sino porque la version que ya tenemos instalada
corrige estos problemas.
