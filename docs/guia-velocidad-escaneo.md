# Prueba de velocidad del escaneo

En esta versión la DSi procesa cada imagen de la cámara mucho más rápido: en
el emulador pasa de 1,5-2,5 segundos a unos 0,2 segundos. Toca comprobarlo en
la consola de verdad.

Copia `dist/para-la-dsi/nds-signer-dev.nds` a la SD (sustituye la anterior).
Usa la **versión de desarrollo**: muestra datos que necesito.

> ⚠️ Seguimos con la **semilla pública de prueba** y en **Signet**.

## 1 · Medidas de la consola

1. Abre NDS-Signer y pulsa **SELECT**.
2. Pulsa **Benchmark** y espera unos segundos.
3. Pulsa **Show as QR** y haz una **foto** del QR a la carpeta `fotos`.

## 2 · Escanear el QR animado de Sparrow

1. En la DSi: *Settings → Advanced → Bitcoin network → Testnet* y carga la
   semilla de prueba (huella `8b218e81`).
2. En Sparrow, monedero `nds-prueba` (o `nds-xpub`), pestaña **Send**: prepara
   un envío como la otra vez, **Create Transaction** →
   **Finalize Transaction for Signing** → **Show QR**.
3. En la DSi: *Scan* y apunta al QR animado. **Cronometra** cuánto tarda.
4. **Mientras escanea**, haz una **foto de la pantalla de abajo**. Debajo del
   progreso aparecen dos líneas de números (`fps ...` y `ms ...`).
5. Cuando termine, pulsa **SELECT** y luego **Show as QR**, y haz otra foto.
   El informe incluye el resumen del último escaneo.

No hace falta enviar la transacción: puedes volver atrás sin firmar.

## Qué me interesa que me cuentes

- Los **segundos** que tardó (la otra vez fueron unos 29).
- Las fotos: el informe del paso 1, la pantalla de abajo durante el escaneo
  y el informe del final.
- Si se lee peor que antes, por ejemplo si tienes que acercarla más o
  sujetarla más quieta.
