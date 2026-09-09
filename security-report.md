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
