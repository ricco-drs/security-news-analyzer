# security-news-analyzer
Laboratorio 1 — Construcción segura de una aplicación Python con pip

## Pruebas realizadas

Se probó la aplicación con tres portales de noticias peruanos y con un dominio
inexistente, para validar en un caso real las correcciones de User-Agent,
encoding y extracción de título, además del manejo de errores.

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
