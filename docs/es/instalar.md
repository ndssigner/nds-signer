# Instalar NDS-Signer

*[Read in English](../install.md)*

## Qué consolas sirven

| Consola | ¿Funciona? | Notas |
| :--- | :---: | :--- |
| Nintendo DS (2004) | ❌ No | 4 MB de memoria: NDS-Signer necesita más de 8 (6 MB para Python y 2 MB de código). Los tonos de teléfono sustituirían a la cámara que le falta, no a la memoria. |
| Nintendo DS Lite | ❌ No | Lo mismo: 4 MB de memoria. |
| Nintendo DSi | ✅ Sí | El mismo hardware que la DSi XL. |
| Nintendo DSi XL (DSi LL en Japón) | ✅ Sí | La consola en la que se prueba NDS-Signer. |
| Nintendo 3DS, 3DS XL, 2DS, New 3DS, New 3DS XL, New 2DS XL | ❓ Sin probar | Ejecutan programas de DSi, pero la cámara, la tapa y el botón de encendido no se han probado con NDS-Signer. Se agradecen pruebas ([help wanted](../help-wanted.md)). |
| Emuladores (melonDS…) | ⚠️ Solo para desarrollo | Un ordenador no está aislado: nunca uses una semilla de verdad en un emulador. |

Cualquier región. Una cámara que funcione escanea los QR; sin ella (o con
ella estropeada), las PSBT y las semillas pueden llegar como
[tonos de teléfono](LEEME.md#tonos-de-teléfono-experimental) (experimental),
por cable o al aire, así que una DSi puede firmar igualmente.

## Qué necesitas

- Una DSi o DSi XL y su cargador.
- Una tarjeta SD (la guía de la DSi explica qué tamaños y formato sirven).
- Un ordenador para preparar la tarjeta.

## 1 · Preparar la consola (una sola vez)

Una DSi solo ejecuta programas de Nintendo hasta que se le instala un
lanzador de homebrew. Sigue **[dsi.cfw.guide](https://dsi.cfw.guide)**, la
guía de la comunidad, desde *Get Started* (está en inglés y en otros
idiomas): instala **Unlaunch**, que permite arrancar programas desde la SD.
Haz la copia de seguridad de la memoria interna (NAND) que propone: es tu
vuelta atrás si algo sale mal.

Opcional: **[TWiLight Menu++](https://wiki.ds-homebrew.com/twilightmenu/installing-dsi)**,
un menú para ver y abrir los programas de la SD.

Descarga estas herramientas solo desde los enlaces de las guías.

## 2 · Descargar NDS-Signer

1. Descarga `nds-signer.nds` y `SHA256.txt` de las
   [versiones publicadas](https://github.com/ndssigner/nds-signer/releases) en GitHub. Las versiones
   oficiales solo se publican ahí.
2. Comprueba el archivo:
   - macOS / Linux: `shasum -a 256 nds-signer.nds`
   - Windows: `certutil -hashfile nds-signer.nds SHA256`

   El resultado tiene que ser la huella de `SHA256.txt`. Si no coincide, no
   uses el archivo. Para la comprobación más fuerte,
   [compílalo tú](../../README.md#build): la misma versión da la misma huella.
3. Copia `nds-signer.nds` a la SD, por ejemplo a la carpeta principal.

## 3 · Arrancarlo

- **Desde Unlaunch:** mantén **A + B** pulsados al encender la DSi; el menú
  de Unlaunch muestra los archivos de la SD: elige `nds-signer.nds`.
- **Desde TWiLight Menu++:** ábrelo como cualquier otro programa. Si así la
  cámara no funciona, arráncalo desde Unlaunch.

La pantalla de inicio muestra **NDS-Signer** y su versión. La luz del wifi se
apaga al arrancar.

## 4 · Primeros pasos

1. *Ajustes → Avanzado → Red Bitcoin*: prueba primero con **Testnet/Signet**.
2. Carga una semilla (*Semillas*) o crea una de prueba (*Herramientas →
   Nueva semilla*).
3. Crea en el ordenador una cartera de solo lectura exportando la xpub
   (*Semillas → tu semilla → Exportar xpub*) y escaneándola con Sparrow.
4. Firma una transacción de prueba: créala en Sparrow, *Escanéala* con la
   DSi, revísala, apruébala y escanea el QR firmado con Sparrow.

Qué carteras sirven: mira el [LEEME](LEEME.md#carteras-compatibles).

## Buenas prácticas

- **Usa la SD solo para NDS-Signer:** solo Unlaunch/TWiLight Menu++ y
  NDS-Signer, todo de fuentes oficiales. Lo que se ejecuta antes que
  NDS-Signer podría manipularlo.
- **Nada de tu semilla en la SD**, nunca: ni fotos ni notas. NDS-Signer no
  escribe en ella.
- **Cierra la tapa al terminar:** NDS-Signer borra su memoria y apaga la
  consola.
- **Actualizar:** sustituye `nds-signer.nds` por la versión nueva,
  después de comprobar su huella.
