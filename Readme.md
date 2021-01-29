Electrum-LTC - Cliente ligero de Litecoin
Electrum-LTC es un puerto de Electrum, la billetera Bitcoin, a Litecoin.

Licencia: Licencia MIT
Autor original: Thomas Voegtlin
Mantenedor de puerto: Pooler
Idioma: Python (> = 3.6)
Inicio: https://electrum-ltc.org/
Empezando
( Si ha venido aquí buscando simplemente ejecutar Electrum, puede descargarlo aquí ).

Electrum-LTC en sí es Python puro, al igual que la mayoría de las dependencias necesarias, pero no todo. Las siguientes secciones describen cómo ejecutar desde la fuente, pero aquí hay un TL; DR:

sudo apt-get install libsecp256k1-0
python3 -m pip install --user. [gui, crypto]
No dependencias de Python puro
Si desea utilizar la interfaz de Qt, instale las dependencias de Qt:

sudo apt-get install python3-pyqt5
Para operaciones de curva elíptica, libsecp256k1 es una dependencia requerida:

sudo apt-get install libsecp256k1-0
Alternativamente, cuando se ejecuta desde un repositorio clonado, se proporciona un script para compilar libsecp256k1 usted mismo:

sudo apt-get install automake libtool
./contrib/make_libsecp256k1.sh
Debido a la necesidad de cifrados simétricos rápidos, se requiere criptografía . Instale desde su administrador de paquetes (o desde pip):

sudo apt-get install python3-cryptography
Si desea soporte de billetera de hardware, vea esto .

Ejecutando desde tar.gz
Si descargó el paquete oficial (tar.gz), puede ejecutar Electrum-LTC desde su directorio raíz sin instalarlo en su sistema; todas las dependencias puras de Python están incluidas en el directorio 'paquetes'. Para ejecutar Electrum-LTC desde su directorio raíz, simplemente haga:

./run_electrum
También puede instalar Electrum-LTC en su sistema, ejecutando este comando:

sudo apt-get install python3-setuptools python3-pip
python3 -m pip install --user.
Esto descargará e instalará las dependencias de Python utilizadas por Electrum-LTC en lugar de utilizar el directorio 'paquetes'. También colocará un ejecutable nombrado electrum-ltcen ~/.local/bin, así que asegúrese de que esté en su PATHvariable.

Versión de desarrollo (clon de git)
Consulte el código de GitHub:

clon de git git: //github.com/pooler/electrum-ltc.git
cd electrum-ltc
actualización del submódulo git --init
Ejecute la instalación (esto debería instalar las dependencias):

python3 -m pip install --user -e.
Crear traducciones (opcional):

sudo apt-get install python-solicitudes gettext
./contrib/pull_locale
Finalmente, para iniciar Electrum-LTC:

./run_electrum
Creación de binarios
Linux (tarball)
Ver contrib/build-linux/sdist/README.md.

Linux (AppImage)
Ver contrib/build-linux/appimage/README.md.

Mac OS X / macOS
Ver contrib/osx/README.md.

Ventanas
Ver contrib/build-wine/README.md.

Androide
Ver contrib/android/Readme.md.
