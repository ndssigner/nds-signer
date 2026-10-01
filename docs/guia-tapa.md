# Prueba: cerrar la tapa borra y apaga

Copia `dist/para-la-dsi/nds-signer.nds` a la SD (sustituye el anterior).

> ⚠️ Solo la **semilla pública de prueba** (huella `8b218e81`).

1. Abre NDS-Signer y carga la semilla de prueba.
2. **Cierra la tapa.** La consola debe **apagarse del todo** en un momento
   (la luz de encendido se apaga). Antes, al cerrar la tapa, la consola se
   dormía con la semilla en memoria.
3. Enciéndela y abre NDS-Signer otra vez: no debe haber ninguna semilla
   cargada (*Semillas* está vacío).
4. Repite con el **botón de encendido**: una pulsación corta mientras usas
   NDS-Signer también debe borrar y apagar.
5. Prueba a cerrar la tapa en mitad de un escaneo (con la cámara
   encendida): también debe apagarse.

Si en algún caso la consola se duerme (luz parpadeando) en vez de
apagarse, dímelo.
