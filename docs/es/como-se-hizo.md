# Cómo se hizo NDS-Signer

*[Read in English](../how-it-was-built.md)*

NDS-Signer lo escribió un modelo de IA (Claude Opus 5.5, en Claude Code)
trabajando con una persona que marcó los objetivos, tomó las decisiones y
probó cada versión en una Nintendo DSi XL de verdad. Esta página cuenta cómo
se llegó hasta aquí, para que cada cual pueda juzgar cuánto fiarse y por
qué.

En resumen: **el código que decide qué se firma no es nuevo.** Es el de
SeedSigner y embit, ejecutado sin modificar. Lo nuevo es la capa que lo hace
funcionar en una DSi, y esa capa se prueba comparándola con el
comportamiento del propio SeedSigner.

## El punto de partida

El proyecto empezó con un encargo escrito:
[../history/original-brief.md](../history/original-brief.md) (en inglés).
Pedía un firmador al estilo SeedSigner para la DSi, en C, con tres reglas
innegociables que se siguen cumpliendo:

- **Nada de red**: no inicializar ni usar nunca el hardware inalámbrico.
- **Sin estado**: no escribir claves, semillas ni transacciones en la SD ni
  en ninguna otra memoria permanente.
- **Sin generador aleatorio del hardware**: la entropía la pone el usuario.

Y una directriz: *no reinventar la rueda*, reutilizar SeedSigner.

## La decisión que lo cambió todo

Las tres primeras fases (driver de la cámara, núcleo ARM7 propio, lectura de
QR con quirc) se escribieron en C, como estaba previsto. Después se
replanteó la idea de *traducir* SeedSigner a C
([architecture.md](../architecture.md), en inglés): la verificación de
transacciones de SeedSigner es la parte que más cambia y la más delicada.
Una traducción a mano siempre iría por detrás de sus arreglos, y cada línea
traducida a mano (o por una IA) es una ocasión de meter un fallo.

Así que, en vez de traducir SeedSigner, NDS-Signer **lo ejecuta**:
MicroPython corre en el procesador ARM9 de la DSi los módulos Python de
SeedSigner y embit, incluidos en la ROM. Una serie de pruebas de concepto
(etiquetas `spike-m1` a `spike-m10`) comprobó cada paso en la DSi emulada:

1. MicroPython funciona en el ARM9 (sin sistema operativo ni coma flotante).
2. embit firma una transacción **idéntica byte a byte** a la de CPython.
3. `PSBTParser`, `DecodeQR` (con QR animados UR) y, al final, el
   `Controller` y las vistas de SeedSigner funcionan sin modificar.
4. Introducir semillas, passphrase, ajustes, normalización Unicode (para las
   passphrases BIP-39) y libsecp256k1 v0.8.

Solo se reescriben las pantallas: las vistas de SeedSigner nunca dibujan,
llaman a `run_screen(ClaseDePantalla, **argumentos)`, y NDS-Signer pone
pantallas con los mismos nombres y argumentos para la interfaz de dos
pantallas táctil. Las adaptaciones mecánicas del código de SeedSigner (a
MicroPython le faltan algunas cosas de Python) se hacen al compilar con
`tools/upy_transform.py`, nunca editando sus archivos. Más adelante, los
menús de NDS-Signer pasaron a ser propios donde la interfaz de la DS lo
pedía (por ejemplo, un único menú *Nueva semilla*); el núcleo sigue siendo
el de SeedSigner.

## Cómo se ha probado

Tres niveles, del más rápido al más real:

- **Tests en el ordenador** (`tests/host`): un simulador de las pantallas y
  los controles de la DSi recorre con el controlador real de SeedSigner
  todos los flujos: escanear, revisar y firmar, introducir semillas,
  SeedQR, passphrase, exportar xpub, explorador de direcciones, copias de
  seguridad, semillas nuevas, ajustes, idiomas. Los resultados se comparan
  con CPython (transacciones firmadas, partes UR) y con los vectores de
  prueba de SeedSigner. Un rastreador pulsa todas las opciones de menú
  posibles. Los tests usan la misma memoria que la ROM.
- **Emulador** (melonDS): una ejecución desatendida teclea la semilla de
  prueba en el teclado táctil, escanea una transacción y la firma; el QR
  firmado se lee de capturas de pantalla y se compara con la referencia.
- **Consola de verdad**: cada función se probó en una DSi XL siguiendo
  guías de prueba paso a paso; los problemas llegaban como
  fotos de la pantalla, a menudo con el informe de error en forma de QR.
  Varios fallos solo aparecieron ahí (lecturas del táctil en el primer
  fotograma, el comportamiento del sensor de la cámara, la falta de
  `/proc/cpuinfo`), y cada uno acabó en un test que lo reproduce. Informes:
  [../history/hardware-reports](../history/hardware-reports/).

Hitos en la consola: primera firma (etiqueta `hw-first-signature`), primera
transacción real de Signet creada en Sparrow y emitida
(`hw-first-signet-tx`), todos los menús comprobados (`hw-menus-verified`),
la interfaz gráfica (`hw-ui-style-a`).

## Qué significa para ti

- La IA escribió la capa de la DSi; no escribió la lógica de Bitcoin.
  Revisa esa capa con espíritu crítico: [architecture.md](../architecture.md)
  explica dónde está.
- Nadie ajeno al proyecto lo ha auditado. Por eso es una versión alfa.
- La compilación es reproducible: puedes comprobar que una versión
  publicada sale de este código.
