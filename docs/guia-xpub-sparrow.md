# Crear el monedero de Sparrow escaneando la DSi

En la prueba anterior copiamos a mano la parte pública de la semilla (el
*xpub*) en Sparrow. Ahora la DSi la muestra como QR y Sparrow la lee con la
cámara del Mac, igual que se hace con un SeedSigner.

> ⚠️ Seguimos con la **semilla pública de prueba** y en **Signet**.

Necesitas la ROM nueva: copia `dist/para-la-dsi/nds-signer-dev.nds` a la SD
(sustituye la anterior).

## 1 · En la DSi: mostrar el xpub

1. *Settings → Advanced → Bitcoin network → Testnet*.
2. Carga la semilla de prueba escaneando su imagen (huella `8b218e81`).
3. *Seeds → 8b218e81 → Export xpub*.
4. Pulsa, por orden: **Single Sig** → **Native Segwit** → **Animated (default)**.
5. Sale un aviso de privacidad: **I understand**.
6. La pantalla de arriba muestra los datos: *Fingerprint 8b218e81* y
   *Derivation m/84'/1'/0'*. Pulsa **Export xpub**.
7. Aparece un QR animado (5 partes). Pulsa **arriba** un par de veces para
   subir el brillo del fondo.

## 2 · En Sparrow: crear un monedero nuevo con ese QR

1. **File → New Wallet**, nombre `nds-xpub`.
2. *Script Type*: **Native Segwit (P2WPKH)**.
3. En *Keystores* elige **Airgapped Hardware Wallet**. En la lista, junto a
   **SeedSigner**, pulsa **Scan...**.
4. Acerca la pantalla de arriba de la DSi a la cámara del Mac hasta que lo lea.
5. Sparrow rellena solo la huella, la derivación y el xpub. Comprueba que la
   huella es **`8b218e81`** y la derivación **`m/84'/1'/0'`**, y pulsa **Apply**.
6. Pestaña **Receive**: la primera dirección debe ser
   **`tb1qw2as76rh4jhykn9zvevdt5tawmqx7hhy7ydvvu`**, la misma que en la prueba
   anterior. En **Transactions** deberían aparecer las monedas de prueba que ya
   tenías: es el mismo monedero.

## Qué me interesa que me cuentes

- Si Sparrow leyó el QR y **cuántos segundos** tardó.
- Si la huella, la derivación y la primera dirección coinciden.
- Cualquier cosa rara: foto a la carpeta `fotos` y me avisas.
