import time
import base64
import ecdsa
from datetime import datetime


def generar_claves():
    """Función para generar las claves pública y privada
    """

    # Clave privada
    clave_privada = ecdsa.SigningKey.generate(
        curve=ecdsa.SECP256k1)
    clave_privada_hexadecimal = clave_privada.to_string().hex()

    # Clave pública
    clave_publica = clave_privada.get_verifying_key()
    clave_publica_hexadecimal = clave_publica.to_string().hex()

    # Codificarlo en base64 para hacerla más corta
    clave_publica_hexadecimal = base64.b64encode(
        bytes.fromhex(clave_publica_hexadecimal))

    # Almacenar claves en archivo
    nombre_archivo = input("Escribe el nombre de tu cartera ") + ".txt"
    with open(nombre_archivo, "w") as f:
        f.write(
            F"direccion_minero = {clave_publica_hexadecimal.decode()}\nclave_privada_minero = {clave_privada_hexadecimal}")
    print(
        F"Tu cartera y clave privada están en {nombre_archivo}")


def cartera():
    """Función cartera
    """

    respuesta = None

    while respuesta not in ["1", "2"]:
        respuesta = input("""¿Qué quieres hacer?
        1. Generar nueva cartera
        2. Salir\n""")

    if respuesta == "1":
        generar_claves()
    else:
        quit()


if __name__ == '__main__':
    print("""=========================================\nSimpleBlockchain v1.0.0\n=========================================\n""")
    cartera()
    input("Pulsa ENTRAR para salir...")
