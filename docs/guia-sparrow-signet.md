# Prueba real con Sparrow (red de pruebas Signet)

Objetivo: usar NDS-Signer como lo usaría cualquiera. Sparrow (en el Mac)
prepara una transacción, la DSi la firma sin conexión y Sparrow la envía. Todo
en **Signet**, una red de pruebas: las monedas no valen nada.

> ⚠️ Seguimos usando la **semilla pública de prueba**. Nada de semillas reales.

## 1 · Instalar Sparrow

Lo más cómodo es con Homebrew, desde la terminal:

```
brew install --cask sparrow
```

O descárgalo **solo** desde su web oficial, **https://sparrowwallet.com**
(sección *Download*, versión para Mac con Apple Silicon).

*(Para esta prueba con monedas sin valor basta. Para usar Sparrow con fondos
reales, verifica la firma de la descarga como explica su web.)*

## 2 · Poner Sparrow en Signet

1. Abre Sparrow. Si te pregunta por el servidor, de momento ciérralo.
2. Menú **Tools → Restart In → Signet**. Sparrow se reinicia en Signet.
3. En la ventana de conexión (o en **Sparrow → Settings → Server**) elige
   **Public Server** y pulsa *Test Connection*: debe decir que conecta.

## 3 · Crear el monedero "de solo lectura"

Sparrow no conoce la semilla: solo su parte pública. La semilla vive en la DSi.

1. **File → New Wallet**, nombre `nds-prueba`.
2. *Script Type*: **Native Segwit (P2WPKH)**.
3. En *Keystores* elige **xPub / Watch Only Wallet** y rellena:
   - **Master fingerprint:** `8b218e81`
   - **Derivation:** `m/84'/1'/0'`
   - **xPub:**
     `tpubDD7jEAawMT9RhWApdGTC3asCkxmu5vuXZSoFvTMTi9tzoQb2ZztgbjgD5uAyZU1RsC7PZABMJc5KgcLrYCTpDmEoaEbVA6aVPpRun8VJKHr`
4. Pulsa **Apply** (si pide contraseña para el archivo del monedero, puedes dejarla vacía).
5. Ve a la pestaña **Receive**. La dirección debe empezar por
   **`tb1qw2as76rh4jhykn9zvevdt5tawmqx7hhy7ydvvu`**. Si coincide, todo cuadra.

## 4 · Conseguir monedas de prueba

1. Copia esa dirección de *Receive*.
2. Abre un grifo de Signet, por ejemplo **https://signetfaucet.com** (o
   **https://alt.signetfaucet.com**), pega la dirección y pide monedas.
3. En Sparrow, pestaña **Transactions**: aparecerán enseguida y quedarán
   confirmadas en unos 10 minutos.

## 5 · Firmar con la DSi

1. En Sparrow, pestaña **Send**: envía **10 000 sats** a cualquier dirección
   (por ejemplo, la siguiente de tu propio *Receive*, o la del grifo para
   devolverlas). Pulsa **Create Transaction** y luego **Finalize Transaction for
   Signing**.
2. Pulsa **Show QR**: Sparrow muestra un **QR animado** en la pantalla del Mac.
3. En la DSi (versión de desarrollo): *Settings → Advanced → Bitcoin network →
   Testnet* y carga la semilla escaneando la imagen de la semilla de prueba
   (como en la guía anterior; huella `8b218e81`). Luego *Scan transaction* y
   apunta la cámara al QR animado de Sparrow. **Cronometra cuánto tarda** en
   leerlo entero (en la parte de abajo va saliendo el progreso).
4. Revisa en la DSi: cantidad enviada, comisión y **cambio** (esta vez sí hay
   cambio que vuelve a tu monedero). Aprueba.
5. La DSi muestra el QR firmado. Pulsa **arriba** varias veces para subir el
   brillo del fondo: al Mac le costará menos leerlo.
6. En Sparrow, en esa misma transacción, pulsa **Scan QR** (usa la cámara del
   Mac; dale permiso si lo pide) y acerca la pantalla de arriba de la DSi a la
   cámara hasta que lo lea.
7. Sparrow mostrará la transacción firmada: pulsa **Broadcast Transaction**.

## Qué me interesa que me cuentes

- Si la DSi leyó el QR animado de Sparrow y **cuántos segundos** tardó.
- Qué mostró la DSi al revisar (una foto de la pantalla con el cambio, si puedes).
- Si Sparrow leyó el QR de la DSi y si la transacción se envió bien (el *txid*
  que muestra Sparrow).
- Cualquier cosa rara: foto a la carpeta `fotos` y me avisas.
