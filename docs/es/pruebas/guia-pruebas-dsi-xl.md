# Probar NDS-Signer en la DSi XL

Guía para la primera prueba en la consola real. No hace falta saber nada
técnico: sigue los pasos, compara lo que ves con lo que pone aquí y, si algo
no coincide o se queda parado, **haz una foto**.

> ⚠️ **Solo datos de prueba.** La semilla de esta guía es pública (la conoce
> todo el mundo) y la transacción es de la red de pruebas. **Nunca metas una
> semilla real** en esta versión.

## Qué necesitas

- La DSi XL cargada.
- Su tarjeta SD (la DSi XL usa tarjetas SD de tamaño normal).
- El Mac, para mostrar en pantalla unos códigos QR de prueba.
- El móvil, para hacer fotos.

En la carpeta `dist` del proyecto están preparados:

| Archivo | Para qué |
| :--- | :--- |
| `para-la-dsi/nds-signer.nds` | La versión normal |
| `para-la-dsi/nds-signer-dev.nds` | La versión de desarrollo (con diagnóstico) |
| `imagenes-para-el-mac/1-transaccion-de-prueba.png` | Transacción de prueba para firmar |
| `imagenes-para-el-mac/2-semilla-de-prueba-SeedQR.png` | Semilla de prueba en forma de QR |

## Paso 0 · ¿La consola está preparada para abrir programas caseros?

Enciende la DSi XL **manteniendo pulsados A y B**.

- Si aparece un menú negro llamado **Unlaunch**: ya está preparada. Sigue al paso 1.
- Si arranca el menú normal de la DSi: hay que prepararla primero. Sigue la
  guía oficial de la comunidad: **https://dsi.cfw.guide/** (en el selector de
  idioma de la web puedes elegir español)
  (instala *Unlaunch* y *TWiLight Menu++*). Hazlo con calma y sin saltarte
  pasos: es el único paso con un pequeño riesgo para la consola. Si tienes
  dudas en algún punto, pregúntame antes de seguir.

## Paso 1 · Copiar NDS-Signer a la tarjeta

1. Apaga la consola y saca la tarjeta SD.
2. Conéctala al Mac.
3. Copia los dos archivos de `dist/para-la-dsi/` a la tarjeta (a la raíz o a la carpeta `nds`).
4. Expulsa la tarjeta y vuelve a ponerla en la consola.

## Paso 2 · Abrir NDS-Signer

- Enciende la consola, entra en **TWiLight Menu++** y elige `nds-signer.nds`.
- Si más adelante la cámara no funciona, prueba a abrirlo desde **Unlaunch**
  (encender con A y B pulsados y elegir el archivo desde ahí).

## Paso 3 · Las pruebas (versión normal)

Abre en el Mac las dos imágenes de `imagenes-para-el-mac` (mejor a pantalla
completa y con el brillo alto). La cámara que usamos es la **exterior**, la
de la tapa de fuera.

| # | Qué haces | Qué debería pasar |
| :--- | :--- | :--- |
| 1 | Abres el programa | Arriba: **Home** y "NDS-Signer". Abajo: botones *Scan, Seeds, Tools, Settings*. |
| 2 | Tocas *Settings* con el lápiz y luego *< Back* | Cambia de pantalla y vuelve. El táctil responde donde tocas. |
| 3 | *Settings* → *Advanced* → *Bitcoin network* → *Testnet* | *Testnet* queda marcado con un `*`. Pulsa **B** varias veces para volver a Home. |
| 4 | *Seeds* → *Scan a SeedQR* y apuntas la cámara a la imagen **2** | Arriba se ve lo que ve la cámara. Al leerla: **Finalize Seed** y huella **8b218e81**. Toca *Done*. |
| 5 | *Scan transaction* y apuntas a la imagen **1** | **Review Transaction**: *Spend 24,857 sats*, *Fee 143 sats*. |
| 6 | *Review details* | Aviso **Full Spend!** (es correcto: la transacción de prueba no tiene cambio). Toca *Continue*. |
| 7 | *Review recipients* | *Will Send (#1)*: 15,000 sats a `2N1Agr9...`. *Next recipient*: 9,857 sats a `tb1qrgky...`. *Next*. |
| 8 | *Approve transaction* | Arriba aparece un **QR que va cambiando** (la transacción firmada). Con arriba/abajo cambia el brillo del fondo. |
| 9 | *Done* y apagas la consola | Vuelve a Home. Al apagar, la semilla desaparece (nada se guarda). |

Si el paso 4 no lee el QR, prueba acercar o alejar la consola, que el QR se vea
entero y sin reflejos. Anota más o menos **cuántos segundos tarda** en leer
cada QR: es lo que más me interesa saber del hardware real.

*(Alternativa al paso 4: Seeds → Enter 12-word seed y teclear las palabras
`height demise useless trap grow lion found off key clown transfer enroll`.
Con 4 letras de cada palabra ya aparece para tocarla.)*

## Paso 4 · La versión de desarrollo

Abre `nds-signer-dev.nds` y repite las pruebas. Tiene tres ayudas:

- **Latido:** en la esquina de abajo a la derecha hay una rayita que gira.
  Si algo parece parado pero la rayita gira, el programa está vivo (esperando
  algo). Si la rayita **también** se para, la consola se ha colgado del todo:
  haz una foto.
- **Diagnóstico:** pulsa **SELECT** en cualquier menú. Toca *Benchmark*
  (tarda unos segundos) y luego *Show as QR*: **haz una foto a ese QR**.
  *Touch test* sirve para comprobar el táctil.
- **Comprobación de la firma:** en el paso 8, debajo del QR aparece
  `check: c1a7570a`. Si sale **exactamente** eso, la firma es correcta.

## Si algo falla

- Si aparece **"NDS-Signer stopped"**: pulsa **A** y sale el error como QR. Haz una foto a ese QR.
- Si se queda parado o ves algo raro: foto de las **dos pantallas**.
- Consejos para las fotos: de frente, sin reflejos, con el QR entero y enfocado.

**Cómo pasármelas:** mándamelas por el chat, o déjalas en la carpeta `fotos`
del proyecto (`~/Desarrollo/nds-signer/fotos`) y dime que ya están. Los QR de
las fotos los leo directamente, no hace falta que copies nada a mano.
