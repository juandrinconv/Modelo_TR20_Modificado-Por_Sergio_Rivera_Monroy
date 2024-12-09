import pandas as pd
import numpy as np

# Funciones polinómicas para los tramos de HUA
def calcular_hua(tt_tp):
    if 0.0 <= tt_tp <= 0.4:
        return 1.375 * tt_tp**2 + 0.225 * tt_tp + 1e-6
    elif 0.4 < tt_tp <= 0.80:
        return -1 * tt_tp**2 + 2.75 * tt_tp - 0.63
    elif 0.80 < tt_tp <= 1.2:
        return -1.75 * tt_tp**2 + 3.5 * tt_tp - 0.75
    elif 1.2 < tt_tp <= 1.6:
        return -0.875 * tt_tp**2 + 1.525 * tt_tp + 0.36
    elif 1.6 < tt_tp <= 2.0:
        return 0.75 * tt_tp**2 - 3.4 * tt_tp + 4.08
    elif 2.0 < tt_tp <= 2.4:
        return 0.1625 * tt_tp**2 - 1.0475 * tt_tp + 1.725
    elif 2.4 < tt_tp <= 2.8:
        return 0.125 * tt_tp**2 - 0.825 * tt_tp + 1.407
    elif 2.8 < tt_tp <= 3.2:
        return 0.0875 * tt_tp**2 - 0.6175 * tt_tp + 1.12
    elif 3.2 < tt_tp <= 3.6:
        return 0.0375 * tt_tp**2 - 0.3025 * tt_tp + 0.624
    elif 3.6 < tt_tp <= 4.0:
        return 0.025 * tt_tp**2 - 0.215 * tt_tp + 0.471
    elif 4.0 < tt_tp <= 5.0:
        return -0.0073 * tt_tp**3 + 0.105 * tt_tp**2 - 0.5112 * tt_tp + 0.8425
    else:
        return 0  # Fuera del rango

# Función para calcular la convolución hidrológica
def calculate_all_Qn(M, P, U):
    vector_Qn = []
    for n in range(1, M + 1):
        if n >= len(P) or n >= len(U):
            vector_Qn.append({n: 0})
        else:
            Qn = sum(P[m - 1] * U[n - m] for m in range(1, n + 1))  # Ajuste de índices
            vector_Qn.append({n: Qn})
    return vector_Qn

# Función principal para cargar y procesar los datos
def cargar_datos_precipitacion():
    ruta_archivo_precipitacion = input("Por favor, ingrese la ruta del archivo .TXT de precipitación: ")
    ruta_parametros = input("Por favor, ingrese la ruta del archivo .TXT con los valores de CN, Lambda (L), tiempo de concentración (Tc), y Qbase: ")
    ruta_datos_observados = input("Por favor, ingrese la ruta del archivo .TXT de datos observados: ")

    try:
        print(f"\nCargando el archivo de precipitación desde: {ruta_archivo_precipitacion}")
        datos = pd.read_csv(ruta_archivo_precipitacion, sep='\t', header=None, names=["Fecha", "Precipitacion"])
        datos['Fecha'] = pd.to_datetime(datos['Fecha'], format='%m/%d/%Y %H:%M', errors='coerce')
        
        if datos['Fecha'].isnull().any():
            raise ValueError("Algunas fechas no pudieron ser convertidas. Verifica el formato de las fechas en el archivo.")
        
        print(f"\nCargando el archivo de parámetros desde: {ruta_parametros}")
        parametros = pd.read_csv(ruta_parametros, sep='\t', header=None, names=["CN", "Lambda", "Tc", "Qbase"])
        
        print(f"\nCargando el archivo de datos observados desde: {ruta_datos_observados}")
        datos_observados = pd.read_csv(ruta_datos_observados, sep='\t', header=None, names=["Fecha", "Qobs"])
        datos_observados['Fecha'] = pd.to_datetime(datos_observados['Fecha'], format='%m/%d/%Y %H:%M', errors='coerce')

        if datos_observados['Fecha'].isnull().any():
            raise ValueError("Algunas fechas no pudieron ser convertidas. Verifica el formato de las fechas en el archivo de datos observados.")
        
        # Verificar que las fechas de precipitación y observados coincidan
        if not datos['Fecha'].equals(datos_observados['Fecha']):
            raise ValueError("Las fechas de los archivos de precipitación y observados no coinciden.")
        
        # Agregar Qobs al DataFrame principal
        datos['Qobs'] = datos_observados['Qobs']

        # Solicitar el área una vez
        area_km2 = float(input("\nIngrese el área en Km²: "))
        
        # Lista para almacenar los resultados de las iteraciones
        resultados_iteraciones = []

        # Iterar sobre cada fila del archivo de parámetros
        for index, row in parametros.iterrows():
            CN, L, tiempo_concentracion, Qbase = row['CN'], row['Lambda'], row['Tc'], row['Qbase']
            
            if CN <= 0 or CN > 100:
                raise ValueError(f"El valor de CN debe estar entre 0 y 100. (Fila {index + 1})")
            if L < 0 or L > 1:
                raise ValueError(f"El valor de Lambda debe estar entre 0 y 1. (Fila {index + 1})")
            if tiempo_concentracion <= 0:
                raise ValueError(f"El tiempo de concentración debe ser positivo. (Fila {index + 1})")

            S = 25400 / CN - 254
            Ia = L * S
            
            # Calcular Precipitación efectiva
            datos['Precipitacion_Acumulada'] = datos['Precipitacion'].cumsum()
            datos['Precipitacion_Efectiva'] = datos.apply(
                lambda row: ((row['Precipitacion_Acumulada'] - Ia) ** 2) / 
                            (row['Precipitacion_Acumulada'] + (1 - L) * S) 
                if row['Precipitacion_Acumulada'] >= Ia else 0, axis=1
            )
            datos['Exceso'] = datos['Precipitacion_Efectiva'].diff().fillna(0)
            datos['Loss'] = datos['Precipitacion'] - datos['Exceso']

            # Calcular variables adicionales
            delta_tiempo = datos['Fecha'].diff().dropna().mode()[0]
            delta_tiempo_horas = delta_tiempo.total_seconds() / 3600
            Tlag = 0.6 * tiempo_concentracion
            Tp = (delta_tiempo_horas / 2) + Tlag
            qp = 0.20833 * area_km2 / Tp
            
            # Tiempo acumulado y HUA
            datos['T'] = [(i + 1) * delta_tiempo_horas for i in range(len(datos))]
            datos['t/tp'] = datos['T'] / Tp
            datos['HUA'] = datos['t/tp'].apply(calcular_hua) * qp
            
            # Usar el Hidrograma Unitario Adimensional (HUA) para la convolución
            P = datos['Exceso'].tolist()  # Precipitación efectiva
            U = datos['HUA'].tolist()  # Hidrograma HUA
            
            # Calcular Qn con la función 'calculate_all_Qn'
            vector_Qn = calculate_all_Qn(len(datos), P, U)
            Qn_values = [list(qn.values())[0] for qn in vector_Qn]
            datos['Q'] = Qn_values

            # Sumar el caudal base
            datos['Q'] += Qbase

            # Cálculo de NSE
            Qobs_mean = datos['Qobs'].mean()
            NSE = 1 - (np.sum((datos['Qobs'] - datos['Q'])**2) / 
                       np.sum((datos['Qobs'] - Qobs_mean)**2))
            uno_menos_NSE = 1 - NSE
            
            # Guardar resultados de esta iteración
            resultados_iteraciones.append((CN, L, tiempo_concentracion, Qbase, NSE, uno_menos_NSE))
        
        # Generar archivo con los resultados
        ruta_guardado = input("\nIngrese la ruta donde desea guardar el archivo de resultados: ")
        archivo_resultados = f"{ruta_guardado}/Resultados Calibración.txt"
        
        with open(archivo_resultados, 'w') as f:
            f.write("CN\tLambda\tTc\tQbase\tNSE\t1-NSE\n")
            for resultado in resultados_iteraciones:
                f.write(f"{resultado[0]}\t{resultado[1]}\t{resultado[2]}\t{resultado[3]}\t{resultado[4]}\t{resultado[5]}\n")
        
        print(f"\nResultados guardados exitosamente en: {archivo_resultados}")
        return datos

    except Exception as e:
        print(f"\nError al cargar los archivos o procesar los datos: {e}")
        return None

# Ejecución principal
resultados = cargar_datos_precipitacion()