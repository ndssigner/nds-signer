# NDS-Signer

**Un firmador de transacciones Bitcoin (PSBT) sin conexión y sin memoria
para la Nintendo DSi, que ejecuta el propio código de
[SeedSigner](https://github.com/SeedSigner/seedsigner).**

*[Read in English](../../README.md)*

> ⚠️ **Versión alfa (v0.1.0-alpha).** Nadie la ha auditado. Pruébala en
> testnet/signet o con cantidades que puedas permitirte perder.

Una Nintendo DSi ya tiene lo que necesita un SeedSigner: cámara, dos
pantallas (una táctil), batería y ninguna red de la que fiarse. De segunda
mano cuesta menos que las piezas de un firmador casero, y en un cajón parece
un juguete viejo, no una cartera de bitcoin. Por qué existe este proyecto:
[por-que.md](por-que.md).

## Capturas

Pantalla de arriba y de abajo de la DSi, dibujadas con las fuentes de la ROM
por el simulador de los tests (textos en inglés; en la consola salen en tu
idioma):

<table>
<tr><td align="center"><img src="../images/home.png" width="190" alt="Inicio"><br><sub>Inicio</sub></td><td align="center"><img src="../images/review.png" width="190" alt="Revisar la transacción"><br><sub>Revisar la transacción</sub></td><td align="center"><img src="../images/recipient.png" width="190" alt="Dirección de cada destinatario"><br><sub>Dirección de cada destinatario</sub></td><td align="center"><img src="../images/math.png" width="190" alt="Las cuentas cuadran"><br><sub>Las cuentas cuadran</sub></td></tr>
<tr><td align="center"><img src="../images/signed-qr.png" width="190" alt="Transacción firmada, QR animado"><br><sub>Transacción firmada, QR animado</sub></td><td align="center"><img src="../images/addresses.png" width="190" alt="Direcciones con su QR"><br><sub>Direcciones con su QR</sub></td><td align="center"><img src="../images/seedqr-map.png" width="190" alt="Copia del SeedQR con mapa"><br><sub>Copia del SeedQR con mapa</sub></td><td align="center"><img src="../images/new-seed.png" width="190" alt="Nueva semilla: garabato + micro"><br><sub>Nueva semilla: garabato + micro</sub></td></tr>
</table>

## Qué hace

- **Firmar transacciones:** escaneas el QR de una transacción preparada en
  una cartera de solo lectura (por ejemplo Sparrow), revisas destinatarios,
  cambio y comisión en la pantalla de arriba, apruebas y la DSi muestra la
  transacción firmada como QR animado.
- **Semillas, solo en memoria:** escribes las 12/24 palabras con el teclado
  táctil o escaneas un SeedQR; puedes añadir passphrase.
- **Semillas nuevas:** con dados, con la cámara o con garabato + micrófono.
- **Copias de seguridad:** ver las palabras, copiar el SeedQR a mano (con un
  mapa del código entero en la pantalla de abajo) y verificar la copia.
- **Cartera:** exportar la xpub como QR, explorador de direcciones (cada una
  con su QR) y verificar una dirección.
- **Ajustes:** red (mainnet, testnet/signet, regtest), unidades, 16 idiomas
  (el de la consola por defecto), sonidos, cámara trasera o frontal.

## Seguridad

- **Sin red:** el código del wifi ni siquiera está incluido, y los chips
  inalámbricos y su luz se apagan al arrancar.
- **Sin memoria:** nada se escribe en la SD ni en la memoria interna. Las
  semillas y las transacciones solo están en la RAM.
- **Cerrar la tapa lo borra todo:** al cerrarla (o pulsar el botón de
  encendido) se sobrescribe la memoria con secretos y la consola se apaga.
- **Sin azar del hardware:** las semillas nuevas salen solo de lo que tú
  pones (dados, imágenes, garabatos, ruido).
- **Compilación reproducible:** cualquiera puede compilar la ROM y comprobar
  que su huella SHA-256 coincide con la publicada.

## Qué necesitas

- Una **Nintendo DSi o DSi XL** con un lanzador de homebrew (Unlaunch y/o
  TWiLight Menu++, ver [dsi.cfw.guide](https://dsi.cfw.guide)). Tiene que
  arrancar en modo DSi para usar la cámara.
- DS y DS Lite: no sirven (sin cámara, poca memoria). 3DS: sin probar.

## Instalar

1. Descarga `nds-signer.nds` y `SHA256.txt` de las versiones publicadas.
2. Comprueba la huella: `shasum -a 256 nds-signer.nds` tiene que dar lo que
   pone en `SHA256.txt`.
3. Copia `nds-signer.nds` a la SD y ábrelo desde Unlaunch o TWiLight Menu++.

## Guías

- [Sparrow en Signet](guia-sparrow-signet.md): firmar una transacción de
  prueba de principio a fin.
- [Pasar la xpub a Sparrow](guia-xpub-sparrow.md): crear la cartera de solo
  lectura escaneando el QR de la DSi.
- [Pruebas en consola](pruebas/): las guías que se usaron para probar cada
  función en una DSi XL.
- [Cómo se hizo](como-se-hizo.md) y [Desarrollo con el
  emulador](desarrollo-emulador.md).

## Donar

NDS-Signer es gratis y no tiene financiación. Los donativos ayudan a que
siga adelante:

<table>
<tr><td align="center"><img src="../images/donate-bitcoin.png" width="180" alt="Bitcoin"><br><b>Bitcoin</b><br><code>bc1qx5snc0wlc8cg9gwxhyx27y6pkru8rnngyq7uja</code></td>
<td align="center"><img src="../images/donate-lightning.png" width="180" alt="Lightning"><br><b>Lightning</b><br><code>ndssigner@coinos.io</code></td></tr>
</table>

Las mismas direcciones están en la aplicación (*Ajustes → Donar*).
NDS-Signer está hecho sobre [SeedSigner](https://github.com/SeedSigner/seedsigner):
apóyalo también en [seedsigner.com](https://seedsigner.com).

## Aviso

NDS-Signer es software experimental, sin garantía de ningún tipo (licencia
MIT). Los autores no se hacen responsables de su uso ni de pérdidas de
fondos. No tiene relación con Nintendo ni con el proyecto SeedSigner.
