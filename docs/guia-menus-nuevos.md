# Prueba de los menús nuevos

Un programa recorrió en el Mac todos los menús de NDS-Signer y encontró
pantallas que fallaban o no mostraban lo importante. Ya están arregladas.
Ahora toca comprobarlas en la consola.

Copia `dist/para-la-dsi/nds-signer-dev.nds` a la SD (sustituye la anterior).

> ⚠️ Solo la **semilla pública de prueba**. En la prueba 3 crearás una
> semilla con dados: úsala solo para probar, nunca le envíes dinero.

Antes de empezar: *Settings → Advanced → Bitcoin network → Testnet* y carga
la semilla de prueba (huella `8b218e81`), como siempre.

## 1 · Copia de seguridad de la semilla

1. *Seeds → 8b218e81 → Backup seed → View seed words → I understand*.
2. Deben salir las 12 palabras numeradas, 4 por página: *height, demise,
   useless, trap, grow, lion, found, off, key, clown, transfer, enroll*.
3. Al final, *Verify*: te pregunta palabras sueltas. Responde y debe acabar
   en **Backup Verified**.

## 2 · SeedQR para copiar en papel

1. *Seeds → 8b218e81 → Backup seed → Export as SeedQR → Standard: 25x25 →
   I understand*.
2. Sale el QR entero. Pulsa **Begin 25x25**: ahora se ve una zona ampliada.
   Muévete con la cruceta (o las flechas de abajo). Arriba y a la izquierda
   se ve el nombre de la zona (por ejemplo B-3).
3. *Done → Confirm SeedQR*: apunta la cámara al **QR entero** que hay en
   `dist/imagenes-para-el-mac/2-semilla-de-prueba-SeedQR.png`. Debe
   confirmar que es la misma semilla.

## 3 · Crear una semilla con dados

1. *Tools → New seed (dice) → 12 words (50 rolls)*.
2. Pulsa 50 números (por ejemplo, `1 2 3 4 5 6` una y otra vez; para
   probar no hace falta tirar dados de verdad).
3. Te enseña las 12 palabras nuevas. Si tecleaste exactamente
   `123456` repetido hasta 50, deben ser: *unveil nice picture region
   tragic fault cream strike tourist control recipe tourist*.

## 4 · Explorador de direcciones

1. *Seeds → 8b218e81 → Address explorer → Native Segwit → Receive
   addresses*.
2. Arriba salen las direcciones completas. Las dos primeras deben ser las
   que viste en Sparrow: `tb1qw2as76rh…` y `tb1qdxl0syr9…`.

## 5 · Verificar una dirección

1. En Sparrow, pestaña *Receive*, pulsa el QR de la dirección para verlo
   grande.
2. En la DSi: *Scan*, apunta al QR y elige la semilla `8b218e81`.
3. Debe buscarla y decir **Address Verified**, con su número (index).

## Qué me interesa que me cuentes

- Si alguna pantalla falla o se ve mal: foto a la carpeta `fotos`.
- Si la zona ampliada del SeedQR (prueba 2) se entiende bien para
  copiarla a mano.
