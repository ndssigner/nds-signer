# Por qué existe NDS-Signer

*[Read in English](../why.md)*

## Inconvenientes del SeedSigner "clásico"

Aunque no dispongo de uno, siempre he pensado que el *SeedSigner* es una herramienta fantástica para asegurar la autocustodia de bitcoin. El inconveniente principal que le encuentro es el de tener que montárselo uno mismo o comprarlo ya fabricado.

Hay dos asuntos bastante sensibles que creo que afectan a la filosofía de *SeedSigner*:

1) **El hardware habitual es muy reconocible**: pese a que es una solución DIY, todo el mundo tiende a la misma configuración de RPI0 + cámara + pulsadores e incluso carcasa. En la mayoría de casos tiene una forma tan reconocible como las *Trezor* o las *Coldcard*. Esto puede suponer una seria amenaza a la denegación plausible: si alguien posee una *SeedSigner*, probablemente posea algo de bitcoin (vulnerable al ataque de la llave inglesa).

2) **El hardware no es multipropósito**: Si tienes una RPI0 con su cámara y sus pulsadores, ¿para qué más vas a utilizarla?. Otra cosa es que tengas la RPI0 en otra aplicación (por ejemplo en una miniconsola con emuladores) y cuando la quieras utilizar como SeedSigner la retires, le añadas provisionalmente los componentes y la microSD que habilitan esa función, pero no va a darse el caso.

También es divertido ver cómo muchos fabricantes de hardware wallets intentan mimetizar la forma de sus wallets con la de otros dispositivos como calculadoras (*ColdCard MK*), Blackberrys (*Coldcard Q*), teléfonos móviles clásicos, smartphones, e-readers, etc. Sin embargo, con los nuevos modelos de IA cada vez más potentes, ya no es necesario que el operador de un scanner de Rayos X sepa o deje de saber qué rayos es ese dispositivo; el propio scanner ya se lo dirá y lo pondrá en alerta.

## Denegación plausible parasitando dispositivos vintage

La motivación real de desarrollar este port de *SeedSigner* para Nintendo DS no es otra que la de reaprovechar un dispositivo que realmente sirve para otra cosa (jugar) y que es relativamente seguro frente a ataques remotos (cosa que actualmente no ofrecen los smartphones) como para albergar un firmador (o incluso una *wallet* para los más atrevidos).

Mi idea original era desarrollar algo para la GameBoy: un hardware open-source con una cámara digital propia que aprovechara la interfaz de la consola para hacer lo mismo que la *SeedSigner*... Pero además de ser una complicación, introduciríamos riesgos en la cadena de suministro como eventuales infiltraciones en el firmware, en el hardware (ya no solo a nivel de chip o de silicio, sino que hasta te añadan *extras*), o que se filtren las direcciones postales a las que se envíen los dispositivos (ya ha pasado con distintos fabricantes como Trezor).

Por eso creo que lo ideal es utilizar consolas antiguas equipadas con cámaras para poder disfrutar de ese software de manera discreta. Salvo que desentone mucho, una consola no levanta ningún tipo de sospecha. Como es software, uno puede descargárselo desde TOR, comprobar su SHA256 y copiar la ROM en la SD sin que nadie te pueda relacionar. Además, el mercado de segunda mano de estas consolas es amplio y se pueden conseguir por precios en torno a los 50 USD. Mucho más barato que montarse una *SeedSigner*.

Animo por lo tanto a otros desarrolladores a seguir esta filosofía: encontrar hardware existente en el que se pueda ejecutar el software de *SeedSigner* sin llamar la atención: videoconsolas (otro candidato sería la PS Vita), cámaras de fotos, cámaras de video, scanners, netbooks, PDAs, etc. 

Siguiendo esta filosofía, tener el *SeedSigner* en dispositivos antiguos (sin internet) y la wallet en dispositivos de última generación es una combinación muy interesante. Sin embargo, al utilizarse códigos QR —que necesitan una cámara en el receptor— perdemos muchas oportunidades. Habría que plantearse la transmisión de datos por audio, infrarrojos, puerto de serie... ¡¡Imaginaos un *SeedSigner* corriendo en una *HP48*, en una *GameBoy* o en un *Commodore 64* sin modificar!!

## Naturaleza del proyecto, administrador y descargo de responsabilidad

Este proyecto está totalmente hecho con **amor y *Vibe Coding*** gracias a la ayuda de **Claude Opus 5.5**. Invito a todo aquel que quiera contribuir o incluso administrar este proyecto a que lo haga.

Yo personalmente no estoy muy familiarizado con el desarrollo open source y desconozco las dinámicas de colaboración. Tampoco tengo el tiempo ni la voluntad de llevar esto a algo más allá de un proyecto de fin de semana: no soy Linus Torvalds.

Dicho esto añado que **no asumo ninguna responsabilidad** sobre el buen o mal uso que se pueda hacer de este software ni de las potenciales pérdidas que un usuario pueda sufrir de sus bitcoin. Por eso he procurado que el núcleo de este sistema se base completamente en el código original de *SeedSigner*.

