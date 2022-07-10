import json
import os
import pandas as pd
from simple_file_checksum import get_checksum
from typing import List
from collections import defaultdict


def procesar_blockchains(ruta):
    """Función para procesar las blockchains de un directorio

    Args:
        ruta (string): Directorio donde se encuentran las blockchains

    Returns:
        file: Archivo .json unificando todas las blockchains
    """

    blockchains = []
    directorio = os.fsencode(ruta)

    # Obtener blockchains
    for archivo in os.listdir(directorio):
        nombre_archivo = os.fsdecode(archivo)
        if nombre_archivo.endswith(".json") and nombre_archivo != "blockchain.json":
            # store SHA256 of it
            blockchains.append(get_checksum(f"{ruta}/{nombre_archivo}"))

    # Comprobar si todas tienen el mismo hash SHA256
    # añadiendolas a un set, solo debe haber una
    if len(set(blockchains)) == 1:

        # Eliminar todos los archivos de las blockchains
        # unificandolas solo en un archivo
        count = 0
        for archivo in os.listdir(directorio):
            nombre_archivo = os.fsdecode(archivo)
            if nombre_archivo.endswith(".json") and nombre_archivo != "blockchain.json":
                # El primer archivo disponible, renombrarlo para el unificado
                if count == 0:
                    os.rename(f"{ruta}/{nombre_archivo}",
                              f"{ruta}/blockchain.json")
                # Eliminar el resto
                else:
                    os.remove(f"{ruta}/{nombre_archivo}")

                count+1

        # Devolver archivo .json unificado
        with open(f"{ruta}/blockchain.json") as json_file:
            return json.load(json_file)

    else:
        print("Error. Las blockchain obtenidas no son similares entre sí. Ha podido ocurrir una bifurcación.")
        return 0

def crear_informe_json(ruta, blockchain):
    """Función para generar el informe experimental en formato .json

    Args:
        ruta (string): Directorio donde se encuentra el archivo de la blockchain a procesar
        blockchain (file): Archivo .json unificado de todas las blockchains
    """

    # Parametros
    mineros = defaultdict(int)
    informe = []
    simple_blockchain = []
    tiempo_de_minado_total = 0
    potencia_computacion_total = 0

    # Iterar el archivo de la blockchain
    for bloque in blockchain:
        if bloque['indice'] == 0:
            continue

        # Almacenar una blockchain más simple
        simple_blockchain.append(
            {
                "indice": bloque['indice'],
                "tiempo_minado": bloque['tiempo_minado'],
                "potencia_computacion": bloque['potencia_computacion'],
                "minado_por": bloque['minado_por']
            }
        )

        # Almacenar información experimentales
        tiempo_de_minado_total += bloque['tiempo_minado']
        potencia_computacion_total += bloque['potencia_computacion']

        minero = bloque['minado_por']

        if not minero in mineros:
            mineros[minero] = 1
        else:
            mineros[minero] += 1

    # Generar .json
    informe.append({
        "blockchain": simple_blockchain
    })

    informe.append({
        "tiempo_de_minado_medio": tiempo_de_minado_total / len(blockchain)
    })

    informe.append({
        "potencia_computacion_media": potencia_computacion_total / len(blockchain)
    })

    informe.append({
        "tiempo_de_minado_total": tiempo_de_minado_total
    })

    informe.append({
        "potencia_computacion_total": potencia_computacion_total
    })

    bloques_minados_por_alfabetico = []

    for minero in sorted(mineros.items()):
        bloques_minados_por_alfabetico.append({
            int((minero)[0]): int((minero)[1])
        })

    informe.append({
        "bloques_minados_por_alfabetico": bloques_minados_por_alfabetico
    })

    bloques_minados_por_ordenados = []

    for minero in sorted(mineros.items(), key=lambda tup: tup[1], reverse=True):
        bloques_minados_por_ordenados.append({
            int((minero)[0]): int((minero)[1])
        })

    informe.append({
        "bloques_minados_por_ordenados": bloques_minados_por_ordenados
    })

    archivo = open(f"{ruta}/informe.json", "w")
    json.dump(informe, archivo, indent=4)


def crear_informe_xlsx(ruta, blockchain):
    """Función para generar el informe experimental en formato .xlsx

    Args:
        ruta (string): Directorio donde se encuentra el archivo de la blockchain a procesar
        blockchain (file): Archivo .json unificado de todas las blockchains
    """

    # Parametros
    mineros = defaultdict(int)
    indice = []
    tiempo_minado = []
    potencia_computacion = []
    minado_por = []

    tiempo_de_minado_total = 0
    potencia_computacion_total = 0

    # Iterar el archivo de la blockchain
    for bloque in blockchain:
        if bloque['indice'] == 0:
            continue

        # Almacenar una blockchain más simple
        indice.append(bloque['indice'])
        tiempo_minado.append(bloque['tiempo_minado'])
        potencia_computacion.append(bloque['potencia_computacion'])
        minado_por.append(bloque['minado_por'])

        # Almacenar información experimentales
        tiempo_de_minado_total += bloque['tiempo_minado']
        potencia_computacion_total += bloque['potencia_computacion']

        minero = bloque['minado_por']

        if not minero in mineros:
            mineros[minero] = 1
        else:
            mineros[minero] += 1

    # Generar .xlsx
    mineros_bloques_minados_por_alfabetico = []
    bloques_bloques_minados_por_alfabetico = []
    for minero in sorted(mineros.items()):
        mineros_bloques_minados_por_alfabetico.append(int((minero)[0]))
        bloques_bloques_minados_por_alfabetico.append(int((minero)[1]))
    tiempo_de_minado_medio = [(tiempo_de_minado_total / len(blockchain))]
    tiempo_de_minado_medio.extend(
        ['']*(len(indice)-len(tiempo_de_minado_medio)))
    tiempo_de_minado_total = [(tiempo_de_minado_total)]
    tiempo_de_minado_total.extend(
        ['']*(len(indice)-len(tiempo_de_minado_total)))
    potencia_computacion_media = [
        (potencia_computacion_total / len(blockchain))]
    potencia_computacion_media.extend(
        ['']*(len(indice)-len(potencia_computacion_media)))
    potencia_computacion_total = [(potencia_computacion_total)]
    potencia_computacion_total.extend(
        ['']*(len(indice)-len(potencia_computacion_total)))
    mineros_bloques_minados_por_alfabetico.extend(
        ['']*(len(indice)-len(mineros_bloques_minados_por_alfabetico)))
    bloques_bloques_minados_por_alfabetico.extend(
        ['']*(len(indice)-len(bloques_bloques_minados_por_alfabetico)))

    df = pd.DataFrame({'Bloque': indice,
                       'T. (s)': tiempo_minado,
                       'Kh/s': potencia_computacion,
                       'Minado': minado_por,
                       '': '',
                       'Minero': mineros_bloques_minados_por_alfabetico,
                       'Bloques': bloques_bloques_minados_por_alfabetico,
                       'T. medio (s)': tiempo_de_minado_medio,
                       'T. total (s)': tiempo_de_minado_total,
                       'Kh/s medio': potencia_computacion_media,
                       'Kh/s total': potencia_computacion_total,
                       })

    writer = pd.ExcelWriter(f"{ruta}/informe.xlsx", engine='xlsxwriter')

    df.to_excel(writer, sheet_name='Datos', index=False)
    workbook = writer.book
    worksheet = writer.sheets['Datos']
    formato1 = workbook.add_format({'num_format': '0'})
    formato2 = workbook.add_format({'num_format': '#,##0.00'})
    worksheet.set_column(0, 0, None, formato1)
    worksheet.set_column(1, 1, None, formato2)
    worksheet.set_column(2, 2, None, formato1)
    worksheet.set_column(3, 3, None, formato1)
    worksheet.set_column(5, 5, 10, formato1)
    worksheet.set_column(6, 6, 10, formato1)
    worksheet.set_column(7, 7, 12, formato2)
    worksheet.set_column(8, 8, 12, formato2)
    worksheet.set_column(9, 9, 12, formato1)
    worksheet.set_column(10, 10, 12, formato1)
    writer.save()


def crear_informes(ruta, blockchain):
    """Función para generar ambos informes experimentales en formato .json y .xlsx

    Args:
        ruta (string): Directorio donde se encuentra el archivo de la blockchain a procesar
        blockchain (file): Archivo .json unificado de todas las blockchains
    """
    try:
        crear_informe_json(ruta, blockchain)
        crear_informe_xlsx(ruta, blockchain)
    except:
        return 0


def limpiar_directorio(ruta):
    """Función para limpiar un directorio

    Args:
        ruta (string): Directorio a limpiar
    """
    
    directorio = os.fsencode(ruta)

    for archivo in os.listdir(directorio):
        nombre_archivo = os.fsdecode(archivo)
        if nombre_archivo.endswith(".json"):
            os.remove(f"{ruta}/{nombre_archivo}")