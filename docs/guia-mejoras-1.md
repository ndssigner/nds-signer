# Prueba de las mejoras (idioma, escaneo, mapa del SeedQR, direcciones)

Copia `dist/para-la-dsi/nds-signer.nds` y `nds-signer-dev.nds` a la SD
(sustituye los anteriores).

> ⚠️ Solo la **semilla pública de prueba** (huella `8b218e81`).

Si tu consola está en español, NDS-Signer ahora arranca en español. Los
nombres de los menús van en español, con el inglés entre paréntesis.

## 1 · Icono y wifi

1. En el menú de la consola, NDS-Signer tiene su propio icono: un lápiz
   negro sobre un cuadrado naranja.
2. Al abrir NDS-Signer, la luz del wifi de la consola debe **apagarse** (si
   estaba encendida) y seguir apagada todo el rato.

## 2 · Idioma

1. Con la consola en español, la pantalla de inicio sale en español
   (*Escanear, Semillas, Herramientas, Ajustes*).
2. *Ajustes → Idioma (Language) → English*: todo pasa a inglés. Vuelve a
   *Español*.
3. Las flechas para pasar de página ahora son **‹ ›** en vez de
   "Prev/Next".
4. En *Ajustes* ya **no** aparecen "Ajustes persistentes" ni "Probar
   dispositivo" (I/O test): no tienen sentido en la DS.

## 3 · Teclados sin parpadeo

1. *Herramientas → Nueva semilla (dados) → 12 palabras*.
2. Pulsa varios números seguidos: la pantalla **no** debe parpadear en
   negro con cada pulsación. Sal con *< Atrás*.
3. Lo mismo al cargar una semilla tecleando palabras (*Semillas → Cargar
   semilla de 12 palabras*).

## 4 · Preparar el escaneo

1. Pulsa *Escanear*. Antes de encenderse la cámara sale una pantalla con
   consejos y dos botones: **Empezar a escanear** y **Cámara: Cámara
   trasera**.
2. Toca *Cámara* para cambiar a la frontal y otra vez para volver a la
   trasera.
3. Pulsa *Empezar a escanear*: se ve la imagen de la cámara y abajo una
   cuenta atrás de 3 segundos. Durante la cuenta atrás no lee nada: es para
   que apuntes y para que la cámara ajuste la luz. Después escanea como
   siempre. Prueba con `1-transaccion-de-prueba.png`.
4. Prueba también con la **cámara frontal** (apunta la pantalla del Mac a la
   cámara de dentro). Dime si lee el QR y si la imagen sale bien o al
   revés.
5. *Ajustes → Preparar escaneo → Desactivado*: al pulsar *Escanear* entra
   directo a la cámara, como antes. La cámara elegida está en
   *Ajustes → Avanzado → Cámara de escaneo*.

## 5 · Mapa del SeedQR

1. *Semillas → 8b218e81 → Respaldar semilla → Exportar como SeedQR →
   25x25 estándar → Entiendo → Empezar 25x25*.
2. Arriba sale la zona ampliada. Abajo, en vez de las flechas, ahora hay un
   **mapa del QR entero** con la zona actual marcada en naranja y su nombre
   (por ejemplo A-1).
3. Toca otra zona del mapa: arriba debe saltar a esa zona. La cruceta
   también sigue funcionando.

## 6 · Listado de direcciones

1. *Semillas → 8b218e81 → Explorador de direcciones → Native Segwit →
   Direcciones de recepción*.
2. Abajo, cada botón tiene el número a la izquierda y la dirección
   abreviada. Arriba sale la dirección seleccionada **entera** y su **QR**,
   con su número (#0).
3. Toca otro botón: se selecciona y arriba cambia la dirección y el QR.
   Tócalo otra vez: se abre su QR en grande. También con la cruceta y A.
4. Escanea el QR pequeño de arriba con Sparrow o con el móvil: debe dar
   `tb1qw2as76rh4jhykn9zvevdt5tawmqx7hhy7ydvvu` para la #0 (puede salir
   en mayúsculas; es la misma dirección).

Mándame fotos a `fotos/` de lo que no se vea bien.
