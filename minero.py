import procesador
import sys
import concurrent.futures
import threading
import json
import os
import logging
import requests
import argparse
from configparser import ConfigParser
from tracemalloc import start
from blockchain import BlockchainMaliciosa as blockchain
from flask import Flask, request, render_template
from time import sleep

################################################
# Parámetros de configuración
################################################

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dificultad", type=int,
                    help="[int] Dificultad: 1, 2, 3, ... Por defecto 5")
parser.add_argument("-m", "--minero", required=True,
                    help="[int] Número de minero: 1, 2, 3, ...")
parser.add_argument("-i", "--iteraciones", type=int,
                    help="[int] Número de iteraciones: 1, 2, 3, ... Por defecto infinitas")
parser.add_argument("-r", "--reemplazar", type=int,
                    help="[int] Número de bloque a reemplazar: 1, 2, 3, ...")
parser.add_argument("-reemplazaren", "--reemplazaren", type=int,
                    help="[int] Número de bloque para empezar a reemplazar: 1, 2, 3, ...")
parser.add_argument("-parar", "--parar",
                    help="Habilitar parar minero al llegar al final. (Por defecto no para)", action='store_true')
parser.add_argument("-lan", "--lan",
                    help="Habilitar LAN mode, otros nodos en la red. Para el procesamiento de archivos. (SOLO 1 NODO POR EXPERIMENTO). Habilitado = procesa archivo local. Deshabilitado = procesa todos los archivos de nodos locales.", action='store_true')
parser.add_argument("-log", "--log",
                    help="Habilitar procesamiento de datos. (SOLO 1 NODO POR EXPERIMENTO)", action='store_true')
parser.add_argument("-nonodos", "--nonodos",
                    help="Deshabilitar nodos. Utilizar en ejecución sola o incompleta.", action='store_true')
parser.add_argument("-noprints", "--noprints",
                    help="Deshabilitar salidas por consola.", action='store_true')

# Establecer parámetros
args = parser.parse_args()

# Dificultad
if not args.dificultad:
    dificultad = 5
else:
    dificultad = args.dificultad

# Numero minero
numero_minero = args.minero

# Iteraciones
if not args.iteraciones:
    # Infinite iteraciones if not specified
    numero_iteraciones = sys.maxsize
    numero_iteraciones_txt = "Infinitas"
else:
    numero_iteraciones = args.iteraciones
    numero_iteraciones_txt = numero_iteraciones

# Reemplazando bloque
reemplazado = ""

if args.reemplazar:
    reemplazando = True
    reemplazado = False
    numero_reemplazo = args.reemplazar
    reemplazar_en = args.reemplazaren

else:
    reemplazando = False

# Deshabilitar console
if args.noprints:
    sys.stdout = open(os.devnull, 'w')


# Configuracion minero
configuracion_minero = ConfigParser()
minero = configuracion_minero.read("./configuracion/mineros/minero-" +
                                   str(numero_minero) + ".ini")

# Configuracion carteras
configuracion_emisor = ConfigParser()
cartera_emisor = configuracion_emisor.read(
    "configuracion/carteras/" + configuracion_minero.get("carteras", "emisor"))

configuracion_receptor = ConfigParser()
cartera_receptor = configuracion_receptor.read(
    "configuracion/carteras/" + configuracion_minero.get("carteras", "receptor"))

configuracion_malicioso = ConfigParser()
cartera_malicioso = configuracion_malicioso.read(
    "configuracion/carteras/" + configuracion_minero.get("carteras", "malicioso"))


################################################
# Rutas
################################################

# App & endpoints
node = Flask(__name__, static_folder="templates/estilos")


@node.route('/', methods=['GET'])
def interfaz_grafica():
    datos_blockchain = []

    for bloque in blockchain.blockchain:
        datos_blockchain.append(bloque.__dict__)

    return render_template('ver-blockchain.html', blockchain=json.dumps(datos_blockchain, separators=(',', ':')))


@node.route('/blockchain', methods=['GET'])
def obtener_blockchain():
    datos_blockchain = []

    for bloque in blockchain.blockchain:
        datos_blockchain.append(bloque.__dict__)

    return json.dumps(datos_blockchain)


# @node.route('/blockchain-maliciosa', methods=['GET'])
# def get_malicious_chain():
#     datos_blockchain = []

#     for bloque in blockchain.blockchain_maliciosa:
#         datos_blockchain.append(bloque.__dict__)

#     return json.dumps(datos_blockchain)


@node.get('/apagado')
def apagado():
    func = request.environ.get('werkzeug.server.shutdown')

    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

    return 'Server shutting down...'


################################################
# Funciones de almacenaje
################################################

def almacenar_blockchain(blockchain):
    """Función para almacenar la Blockchain en un fichero

    Args:
        blockchain (Blockchain): Blockchain a almacenar
    """

    datos_blockchain = []

    for bloque in blockchain.blockchain:
        datos_blockchain.append(bloque.__dict__)

    file = open("resultados/normal/blockchains/blockchain-" +
                str(numero_minero) + ".json", "w")
    json.dump(datos_blockchain, file, indent=4)


def almacenar_blockchain_maliciosa(blockchain):
    """Función para almacenar la Blockchain maliciosa en un fichero

    Args:
        blockchain (Blockchain): Blockchain a almacenar
    """

    datos_blockchain = []

    for bloque in blockchain.blockchain_maliciosa:
        datos_blockchain.append(bloque.__dict__)

    file = open("resultados/malicioso/blockchains/blockchain-" +
                str(numero_minero) + ".json", "w")
    json.dump(datos_blockchain, file, indent=4)

################################################
# Función maliciosa
################################################


def modificar_bloque_blockchain(blockchain, numero_bloque):
    """Función para modificar un bloque en la Blockchain

    Args:
        blockchain (Blockchain): Blockchain a modificar
        numero_bloque (integer): Número de bloque a modificar
    """

    with blockchain._lock:

        # Añadir transaccion recompensa al listado de transacciones maliciosas
        blockchain.anadir_recompensa_transaccion_maliciosa()

        # Añadir transaccion maliciosa al listado de transacciones maliciosas
        blockchain.anadir_transaccion_maliciosa(configuracion_emisor.get('configuracion', 'direccion_cartera'),
                                                configuracion_emisor.get('configuracion', 'clave_privada_cartera'), configuracion_malicioso.get('configuracion', 'direccion_cartera'), "10", "Transaccion maliciosa")

        blockchain.recalcular_blockchain(numero_bloque)

################################################
# Función minado
################################################


def minar_blockchain(blockchain):
    """Función de minado desde el minero, haciendo uso de diveras funciones de la Blockchain

    Args:
        blockchain (list): Blockchain a minar
    """
    # Si existe orden de reemplazo
    if reemplazando:
        reemplazado = False

    # Si modo nodos activado (por defecto)
    if not args.nonodos:
        nodos_listos = False

        # Esperar al resto de nodos
        while not nodos_listos:
            if len(blockchain.encontrar_nuevas_blockchains()) != 0:
                print("Esperando al resto de nodos...\n")
                print(
                    f"Nodos no listos aún: {blockchain.encontrar_nuevas_blockchains()}")
                sleep(2)
            else:
                nodos_listos = True

    # Bucle para minar en base a las iteraciones
    while blockchain.ultimo_bloque.indice < numero_iteraciones:
        print("---------------------")

        # Si existe orden de reemplazo y aún no ha habido reemplazo
        if reemplazando and not reemplazado:
            # Si llegamos al bloque el cual marca el inicio del intento de reemplazo
            if reemplazar_en <= blockchain.ultimo_bloque.indice:
                modificar_bloque_blockchain(blockchain, numero_reemplazo)
                reemplazado = True
                print("---------------------")
                continue

        # Transaccion recompensa
        blockchain.anadir_transaccion_recompensa()

        # Fake pending transaction
        blockchain.anadir_nueva_transaccion(configuracion_emisor.get('configuracion', 'direccion_cartera'),
                                            configuracion_emisor.get('configuracion', 'clave_privada_cartera'), 
                                            configuracion_receptor.get('configuracion', 'direccion_cartera'), "0.02", "Transaccion normal")

        # blockchain.minar()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            for index in range(1):
                executor.submit(blockchain.minar)

    almacenar_blockchain(blockchain)

    # Si existe orden de reemplazo, se almacena la blockchain maliciosa
    if args.reemplazar:
        almacenar_blockchain_maliciosa(blockchain)
    print("\n---------------------")


################################################
# Función generación de informes
################################################


def intentar_creacion_informes():
    """Función para intenter la creación de informes a partir de las funciones de creación de informes
    """
    # Obtener nodos de la red
    nodos = configuracion_minero.get('configuracion', 'listado_nodos')
    if "," in nodos:
        listado_nodos = nodos.split(",")
    else:
        listado_nodos = [nodos]

    _, _, files = next(os.walk("resultados/normal/blockchains"))
    contador_archivos = len(files)

    # No modo LAN
    if not args.lan:
        nodos_listos = False

        # Esperar a que los nodos estén listos
        while not nodos_listos:

            # Si solo hay un nodo, procesamos un archivo
            if args.nonodos:
                blockchain = procesador.procesar_blockchains(
                    "resultados/normal/blockchains")
                procesador.crear_informes(
                    "resultados/normal/informes", blockchain)
                nodos_listos = True
                continue

            # Si hay varios nodos, espera de nodos...
            if (len(listado_nodos) + 1) != contador_archivos:
                _, _, files = next(os.walk("resultados/normal/blockchains"))
                contador_archivos = len(files)
                print(contador_archivos)
                print(len(listado_nodos) + 1)
                sleep(2)
            else:
                blockchain = procesador.procesar_blockchains(
                    "resultados/normal/blockchains")
                procesador.crear_informes(
                    "resultados/normal/informes", blockchain)
                nodos_listos = True

    # Modo LAN, solo procesamos un archivo
    else:
        blockchain = procesador.procesar_blockchains(
            "resultados/normal/blockchains")
        procesador.crear_informes("resultados/normal/informes", blockchain)

    # Si hay orden de reemplazo, generamos informes maliciosos
    if args.reemplazar:
        blockchain = procesador.procesar_blockchains(
            "resultados/malicioso/blockchains")
        procesador.crear_informes("resultados/malicioso/informes", blockchain)
        nodos_listos = True

################################################
# Funciones de inicializado
################################################


def iniciar_app(blockchain):
    """Función para inicializar la aplicación

    Args:
        blockchain (list): Blockchain utilizada en la aplicación
    """

    # Evitar salida por consola de POST/GET
    logging.getLogger('werkzeug').disabled = True
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'

    node.run(debug=False, port=blockchain.puerto,
             use_reloader=False, host="0.0.0.0")


def inicializar_blockchain():
    """Función para inicializar la blockchain

    Returns:
        Blockchain: Blockchain a utilizar en la ejecución
    """

    # Configuración inicial
    ip = configuracion_minero.get('configuracion', 'ip')
    puerto = configuracion_minero.getint('configuracion', 'puerto')
    nodes = configuracion_minero.get('configuracion', 'listado_nodos')
    listado_nodos = ""

    if "," in nodes:
        listado_nodos = nodes.split(",")
    else:
        listado_nodos = [nodes]

    direccion_minero = configuracion_minero.get('minero', 'direccion_minero')
    clave_privada_minero = configuracion_minero.get(
        'minero', 'clave_privada_minero')

    bc = blockchain(
        dificultad, ip, puerto, listado_nodos, numero_minero, direccion_minero, clave_privada_minero)

    return bc


if __name__ == '__main__':
    print(
        f"|------ PÁRAMETROS INICIALES ------|\n| Minero número: {numero_minero} | Iteraciones {numero_iteraciones_txt} | ")

    if reemplazando:
        print(f"| Reemplazo: Sí | Bloque a reemplazar: {numero_reemplazo} |")
    else:
        print(f"| Reemplazo: No")

    print("\n")

    # Si hay orden de procesar, limpieza primera
    if args.log:
        procesador.limpiar_directorio("resultados/normal/blockchains")
        procesador.limpiar_directorio("resultados/malicioso/blockchains")

    blockchain = inicializar_blockchain()

    first = threading.Thread(target=iniciar_app, args=(blockchain,))
    first.start()

    second = threading.Thread(target=minar_blockchain, args=(blockchain,))
    second.start()
    second.join()

    # Si hay orden de procesar, generar informes al final
    if args.log:
        intentar_creacion_informes()

    # Si existe orden de parar, parado final
    if args.parar:
        sleep(30)
        requests.get(
            url=f"http://{blockchain.ip}:{blockchain.puerto}/apagado", timeout=1)