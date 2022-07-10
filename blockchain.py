import copy
import time
import requests
import threading
import json
import base64
import ecdsa

from requests.exceptions import ConnectionError
from datetime import datetime
from flask import Flask, request
from pympler import asizeof
from hashlib import new, sha256


################################################
# Bloque
################################################


class Bloque:
    def __init__(self, indice, transacciones, attr=None):
        """Inicializador de Bloque

        Args:
            indice (integer): Índice de bloque
            transacciones (list): Listado de transacciones
            attr (Block, optional): Objeto a transformar en bloque. Por defecto no existe.
        """

        if attr is None:
            # Parámetros necesarios
            self.indice = indice
            self.tamano = ""
            self.cabecera = ""
            self.contador_transacciones = len(transacciones)
            self.transacciones = transacciones

            # Parámetros extra
            self.hash = ""
            self.tiempo_minado = ""
            self.potencia_computacion = ""
            self.minado_por = ""

        # Construir bloque a partir de objeto
        else:
            for key, value in attr.items():
                setattr(self, key, value)

    def construir_cabecera(self, hash_previo, transacciones_raiz_merkle, dificultad):
        """Función para construir la cabecera de bloque y establecerla

        Args:
            hash_previo (string): Hash del bloque anterior
            transacciones_raiz_merkle (list): Listado de transacciones a almacenar en arbol merkle ficticio
            dificultad (integer): Dificultad actual de la blockchain

        Returns:
            list: Cabecera
        """

        # Establecer cabecera
        self.cabecera = {"version": 1, "hash_previo": hash_previo, "raiz_merkle": sha256(
            str(transacciones_raiz_merkle).encode()).hexdigest(), "timestamp": time.time(), "dificultad": dificultad, "nonce": 0}

        return self.cabecera

    def calcular_hash(self):
        """Función para calcular el hash de bloque y establecerlo

        Returns:
            string: Hash de bloque
        """

        # Establecer doble SHA256 de la cabecera
        self.hash = sha256(str(
            sha256(json.dumps(str(self.cabecera)).encode()).hexdigest()).encode()).hexdigest()

        return self.hash

    def calcular_tamano(self):
        """Función para calcular el tamaño del bloque y establecerlo

        Returns:
            integer: Tamaño del bloque
        """

        # Establecer tamaño
        self.tamano = asizeof.asizeof(self)

        return self.tamano

################################################
# Blockchain
################################################


class Blockchain():

    def __init__(self, dificultad, ip, puerto, listado_nodos, numero_minero, direccion_minero, clave_privada_minero):
        """Inicializador de la Blockchain

        Args:
            dificultad (int): Dificultad de la Blockchain
            ip (string): Dirección IP del minero que trabaja sobre la Blockchain
            puerto (integer): Puerto del minero que trabaja sobre la Blockchain
            listado_nodos (list): Listado de nodos conectados al minero
            numero_minero (integer): Número identificativo del minero
            direccion_minero (string): Dirección de la cartera del minero, utilizada para la transacción recompensa
            clave_privada_minero (string): Clave privada de la cartera del minero, utilizada para la transacción recompensa
        """

        # Parametros
        self.dificultad = dificultad
        self.ip = ip
        self.puerto = puerto
        self.listado_nodos = listado_nodos
        self.numero_minero = numero_minero.split("-")[0]
        self.direccion_minero = direccion_minero
        self.clave_privada_minero = clave_privada_minero
        # Transacciones
        self.transacciones_no_confirmadas = []
        # Blockchain propia
        self.blockchain = []
        # Otras blockchains
        self.blockchains_nodos = []
        # Multithreading
        self._lock = threading.Lock()
        # Inicio creación bloque Génesis
        self.generar_bloque_genesis()

    def generar_bloque_genesis(self):
        """Función que inicializa el bloque Génesis
        """

        print(
            f"|------ GENERANDO BLOCKCHAIN... ------|\n| Dificultad: {self.dificultad}\t | Puerto: {self.puerto} | Nodos: {self.listado_nodos} |")

        print("\n|------ GENERANDO BLOQUE GÉNESIS... ------|")

        # Valores preestablecidos
        genesis_block = Bloque(0,
                               [self.obtener_transaccion_genesis()])
        genesis_block.construir_cabecera(
            "0000000000000000000000000000000000000000000000000000000000000000", self.obtener_transaccion_genesis(), self.dificultad)
        genesis_block.cabecera["timestamp"] = 1654065166.5091279
        genesis_block.cabecera["nonce"] = 4266222
        genesis_block.hash = "0000000000000000000000000000000000000000000000000000000000000001"
        genesis_block.calcular_tamano()

        genesis_block.tiempo_minado = "-"
        genesis_block.potencia_computacion = "-"
        genesis_block.minado_por = "-"

        # Añadir bloque Génesis a la Blockchain
        self.blockchain.append(genesis_block)

        print("¡Bloque génesis generado!\n")

    ################################################
    # Funciones Prueba de Trabajo
    ################################################

    def es_hash_valido(self, bloque, hash):
        """Función que comprueba si un hash asociado a un bloque es válido

        Args:
            bloque (Bloque): Bloque a comprobar
            hash (string): Hash de bloque a validar

        Returns:
            bool: True o False
        """

        return (hash.startswith('0' * self.dificultad) and
                hash == bloque.calcular_hash())

    def prueba_de_trabajo(self, bloque, verificador=True):
        """Función del algoritmo prueba de trabajo

        Args:
            bloque (Bloque): Bloque a trabajar

        Returns:
            string: Hash válido de bloque
        """
        hash_calculado = bloque.calcular_hash()

        while not hash_calculado.startswith('0' * self.dificultad):
            bloque.cabecera['nonce'] += 1
            hash_calculado = bloque.calcular_hash()

            if bloque.cabecera['nonce'] % int(('1' * self.dificultad)) == 0 and verificador:
                if self.consenso():
                    return 0

        return hash_calculado

    ################################################
    # Funciones de bloque
    ################################################

    @property
    def ultimo_bloque(self):
        """Función para obtener el último bloque de la Blockchain

        Returns:
            Bloque: Último bloque de la Blockchain
        """
        return self.blockchain[-1]

    def anadir_bloque(self, bloque, hash):
        """Función para añadir un bloque a la Blockchain

        Args:
            bloque (Bloque): Bloque a añadir
            hash (string): Hash del bloque a añadir

        Returns:
            bool: True o False
        """

        # Comprobar hash previo de la cabecera
        hash_previo = self.ultimo_bloque.hash

        if hash_previo != bloque.cabecera["hash_previo"]:
            return False

        # Comprobar validez hash
        if not self.es_hash_valido(bloque, hash):
            return False

        # Añadir a la Blockchain
        self.blockchain.append(bloque)

        return True

    ################################################
    # Funciones de transacciones
    ################################################

    def anadir_nueva_transaccion(self, emisor, clave_privada, receptor, cantidad, concepto):
        """Función para añadir una nueva transacción al listado de transacciones no confirmadas

        Args:
            emisor (string): Emisor de la transacción
            clave_privada (string): Clave privada utilizada en la transacción
            receptor (string): Receptor de la transacción
            cantidad (string): Cantidad de la transacción
            concepto (string): Concepto de la transacción
        """

        # Comprobar longitud
        if len(clave_privada) == 64:

            firma, fecha = self.firmar_transaccion_ECDSA(clave_privada)

            transaction = [f"De: {emisor}", f"Para: {receptor}",
                           f"Cantidad: {cantidad}", f"concepto: {concepto}", f"Fecha: {fecha}"]

            if self.verificar_firma(emisor, firma.decode(), fecha):
                self.transacciones_no_confirmadas.append(transaction)
            else:
                print("Transacción fallida. Firma no válida.")
        else:
            print("¡Dirección errónea o longitud de clave no válida!")

    def firmar_transaccion_ECDSA(self, clave_privada):
        """Función para firmar una transacción

        Args:
            clave_privada (string): Clave privada utilizada en la transacción

        Returns:
            string, string: Firma y mensaje codificados
        """

        # Obtener el timestamp actual en string, codificarlo y añadirlo a la firma
        fecha = str(datetime.now())
        fecha_codificada = fecha.encode()

        clave_firmado = ecdsa.SigningKey.from_string(
            bytes.fromhex(clave_privada), curve=ecdsa.SECP256k1)

        firma = base64.b64encode(clave_firmado.sign(fecha_codificada))

        return firma, fecha

    def verificar_firma(self, clave_publica, firma, fecha):
        """Función para verificar la firma de una transacción

        Args:
            clave_publica (string): Clave pública de la transacción
            firma (string): Firma en base64
            fecha (string): Fecha firmado

        Returns:
            bool: True o False
        """

        clave_publica = (base64.b64decode(clave_publica)).hex()
        firma = base64.b64decode(firma)

        comprobar_clave_firmado = ecdsa.VerifyingKey.from_string(
            bytes.fromhex(clave_publica), curve=ecdsa.SECP256k1)

        try:
            return comprobar_clave_firmado.verify(firma, fecha.encode())
        except:
            return False

    def obtener_transaccion_genesis(self):
        """Función para obtener la transacción Genesis por defecto

        Returns:
            list: Transacción Génesis
        """

        return ["De: Red blockchain", f"Para: Nadie", "Cantidad: 50", "Concepto: Transaccion Genesis", f"Fecha: Indeterminado"]

    def obtener_transaccion_recompensa(self):
        """Función para obtener la transacción recompensa por defecto

        Returns:
            list: Transacción recompensa
        """

        return ["De: Red blockchain", f"Para: {self.direccion_minero}", "Cantidad: 50", "Concepto: Transaccion recompensa", f"Fecha: {str(datetime.now())}"]

    def anadir_transaccion_recompensa(self):
        """Función para añadir la transacción recompensa al listado de transacciones no confirmadas
        """

        transaction = self.obtener_transaccion_recompensa()
        self.transacciones_no_confirmadas.append(transaction)

    ################################################
    # Funciones de Consenso
    ################################################

    def consenso(self):
        """Función que realiza el Consenso

        Returns:
            bool: True o False, True si existe otra Blockchain ganadora que no sea la del minero
        """
        # print("\nBuscando consenso...")

        # 1 - Más larga la del minero, por ahora
        blockchain_mas_larga = self.blockchain

        # 2 - Buscar nuevas blockchains
        self.encontrar_nuevas_blockchains()

        # 3 - Obtener la Blockchain más larga con el menor timestamp
        for blockchain in self.blockchains_nodos:
            if(len(blockchain_mas_larga) < len(blockchain)):
                blockchain_mas_larga = blockchain

            # La Blockchain del minero mide igual que la más larga pero diferente timestamp
            elif(len(blockchain_mas_larga) == len(blockchain) and (blockchain_mas_larga[-1].cabecera['timestamp'] != blockchain[-1].cabecera['timestamp'])):
                # Si el timestamp de la más larga es mayor que el comparado
                if(blockchain_mas_larga[-1].cabecera['timestamp'] > blockchain[-1].cabecera['timestamp']):
                    blockchain_mas_larga = blockchain

        # 4 - Comparamos la blockchain más larga con la nuestra
        # La blockchain más larga no es la nuestra
        if(len(blockchain_mas_larga) > len(self.blockchain)):
            self.reemplazar_blockchain(blockchain_mas_larga)
            return True

        # La Blockchain del minero mide igual que la más larga
        elif(((len(blockchain_mas_larga) == len(self.blockchain)) and (blockchain_mas_larga[-1].cabecera['timestamp'] != self.ultimo_bloque.cabecera['timestamp']))):
            # Nuestra blockchain no es la que tiene menor timestamp
            if(self.ultimo_bloque.cabecera['timestamp'] > blockchain_mas_larga[-1].cabecera['timestamp']):
                self.reemplazar_blockchain(blockchain_mas_larga)
                return True

        # Si nada de lo anterior sucede, nuestra blockchain es la más larga
        elif(((len(blockchain_mas_larga) == len(self.blockchain)) and (self.ultimo_bloque.cabecera['timestamp'] == blockchain_mas_larga[-1].cabecera['timestamp']))):
            return False

    def encontrar_nuevas_blockchains(self):
        """Función para encontrar nuevas Blockchains en los nodos

        Returns:
            list: Nodos no listos aún
        """

        nodos_no_listos = []

        for url_nodo in self.listado_nodos:
            blockchain = []
            try:
                # bytes
                blockchain_exportada = requests.get(
                    url=url_nodo + "/blockchain", timeout=1).content
                # bytes a json
                blockchain_exportada = json.loads(blockchain_exportada)
                # información a Bloque
                for bloque in blockchain_exportada:
                    bloque_copiado = Bloque(0, 0, bloque)
                    blockchain.append(bloque_copiado)
                validado = self.es_blockchain_valida(blockchain)
                if validado:
                    self.blockchains_nodos.append(blockchain)

            except ConnectionError:
                nodos_no_listos.append(url_nodo)

        return nodos_no_listos

    def es_blockchain_valida(self, blockchain):
        """Función para comprobar si una Blockchain es válida

        Args:
            blockchain (list): Blockchain a comprobar

        Returns:
            bool: True o False
        """

        for bloque in blockchain:
            if not self.es_hash_valido(bloque, bloque.hash):
                if bloque.indice == 0:
                    continue
                return False
        return True

    def reemplazar_blockchain(self, blockchain):
        """Función para reemplazar la Blockchain del minero por otra

        Args:
            blockchain (list): Blockchain a reemplazar
        """

        self.blockchain = blockchain

    ################################################
    # Funciones de minado
    ################################################
    def minar(self):
        """Función para minar

        Returns:
            bool: False si no hay transacciones a añadir
        """

        with self._lock:
            inicio = time.time()
            if not self.transacciones_no_confirmadas:
                return False

            # Creación de bloque
            nuevo_bloque = Bloque(indice=self.ultimo_bloque.indice + 1,
                                  transacciones=self.transacciones_no_confirmadas
                                  )

            nuevo_bloque.construir_cabecera(
                self.ultimo_bloque.hash, self.transacciones_no_confirmadas, self.dificultad)

            print(f"\nMinando bloque {(self.ultimo_bloque.indice + 1)}...")

            self.prueba_de_trabajo(nuevo_bloque, True)
            self.transacciones_no_confirmadas = []
            fin = time.time()
            total = fin - inicio

            # Parámetros experimentales al bloque
            nuevo_bloque.tiempo_minado = round(total, 2)

            potencia_computacion = round(
                (nuevo_bloque.cabecera['nonce'] / total) / 1000)
            nuevo_bloque.potencia_computacion = potencia_computacion
            nuevo_bloque.minado_por = self.numero_minero

            nuevo_bloque.calcular_tamano()

            # Comprobar que hash es válido y no es 0 por Consenso
            if (self.es_hash_valido(nuevo_bloque, nuevo_bloque.hash)):
                self.anadir_bloque(nuevo_bloque, nuevo_bloque.hash)

                print(
                    f'¡Hash encontrado! [{"{:.3f}".format(total)}s, {potencia_computacion} Kh/s], nonce: {nuevo_bloque.cabecera["nonce"]}')

            # Consenso final
            self.consenso()


################################################
# Blockchain Maliciosa
################################################
class BlockchainMaliciosa(Blockchain):

    # Copia de Blockchain y transacciones maliciosas
    blockchain_maliciosa = []
    transacciones_maliciosas = []

    def recalcular_blockchain(self, indice):
        """Función para recalcular la Blockchain a raíz de un bloque modificado

        Args:
            indice (integer): Índice del bloque a modificar
        """
        blockchain = copy.deepcopy(self.blockchain)
        hash_previo = ""

        inicio = time.time()
        total = 0

        print(f"\nReemplazando bloque... {indice}")
        
        hash_previo = ""
        for bloque in blockchain:

            if bloque.indice < indice:
                self.blockchain_maliciosa.append(bloque)
            else:
                nuevo_bloque = bloque

                if bloque.indice == indice:
                    nuevo_bloque.transacciones = self.transacciones_maliciosas
                    nuevo_bloque.construir_cabecera(
                        nuevo_bloque.cabecera["hash_previo"], nuevo_bloque.transacciones, nuevo_bloque.cabecera["dificultad"])
                    self.prueba_de_trabajo(nuevo_bloque, False)
                    nuevo_bloque.minado_por = self.numero_minero

                if bloque.indice > indice:
                    nuevo_bloque.cabecera["hash_previo"] = hash_previo
                    self.prueba_de_trabajo(nuevo_bloque, False)

                if bloque.indice == self.ultimo_bloque.indice:
                    nuevo_bloque.cabecera["hash_previo"] = hash_previo
                    self.prueba_de_trabajo(nuevo_bloque, False)
                    fin = time.time()
                    total = fin - inicio
                    nuevo_bloque.tiempo_minado = total

                hash_previo = nuevo_bloque.hash

                self.blockchain_maliciosa.append(nuevo_bloque)

        self.blockchain = self.blockchain_maliciosa

        print(f'¡Bloque reemplazado! [{"{:.3f}".format(total)}s]')
        print(f"Longitud blockchain maliciosa: {len(self.blockchain)}")

        self.consenso()

    def anadir_transaccion_maliciosa(self, emisor, clave_privada, receptor, cantidad, concepto):
        """Función para añadir una nueva transacción maliciosa al listado de transacciones maliciosas

        Args:
            emisor (string): Emisor de la transacción
            clave_privada (string): Clave privada utilizada en la transacción
            receptor (string): Receptor de la transacción
            cantidad (string): Cantidad de la transacción
            concepto (string): Concepto de la transacción
        """

        if len(clave_privada) == 64:

            firma, transaccion = self.firmar_transaccion_ECDSA(clave_privada)

            transaction = [f"De: {emisor}", f"Para: {receptor}",
                           f"Cantidad: {cantidad}", f"concepto: {concepto}", f"Fecha: {transaccion}"]

            if self.verificar_firma(emisor, firma.decode(), transaccion):
                self.transacciones_maliciosas.append(transaction)
            else:
                print("Transacción fallida. Firma no válida.")
        else:
            print("¡Dirección errónea o longitud de clave no válida!")

    def anadir_recompensa_transaccion_maliciosa(self):
        """Función para añadir la transacción recompensa al listado de transacciones maliciosas
        """
        transaction = self.obtener_transaccion_recompensa()
        self.transacciones_maliciosas.append(transaction)