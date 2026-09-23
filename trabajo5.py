import datetime
import random
import pytz

mexico_tz = pytz.timezone('America/Mexico_City')
fecha_inicio = datetime.datetime.now(mexico_tz)

print("=" * 55)
print("        SISTEMA EXPERTO DE DIAGNOSTICO")
print("=" * 55)
print(f"\nFecha y hora de inicio: {fecha_inicio.strftime('%d/%m/%Y %H:%M:%S')}")

contador_reportes = 0

def obtener_pregunta(opciones):
    """Retorna una pregunta aleatoria de una lista de opciones."""
    return random.choice(opciones)

def realizar_diagnostico():
    global contador_reportes
    
    contador_reportes += 1
    num_reporte = contador_reportes
    fecha_diagnostico = datetime.datetime.now(mexico_tz)
    
    print("\n" + "=" * 55)
    print("             BIENVENIDO AL SISTEMA")
    print("=" * 55)
    
    print("\nHola, vamos a realizar un diagnostico medico.")
    print("Primero necesito algunos datos.\n")
    
    nombre_completo = input("Cual es tu nombre completo? ")
    
    while True:
        try:
            edad = int(input("Cuantos años tienes? "))
            if edad >= 0:
                break
            else:
                print("La edad no puede ser negativa. Intenta de nuevo.")
        except ValueError:
            print("Por favor ingresa un numero valido.")
    
    direccion = input("Cual es tu direccion? ")
    num_seguro = input("Cual es tu numero de seguro social? ")
    hospital = input("A que hospital estas filiado? ")
    
    if edad < 2:
        rango_edad = "Bebe"
    elif edad < 12:
        rango_edad = "Niño"
    elif edad < 18:
        rango_edad = "Adolescente"
    elif edad < 60:
        rango_edad = "Adulto"
    else:
        rango_edad = "Adulto mayor"
    
    print("\n" + "=" * 55)
    print("             DATOS REGISTRADOS")
    print("=" * 55)
    print(f"Nombre completo: {nombre_completo}")
    print(f"Edad: {edad} años ({rango_edad})")
    print(f"Direccion: {direccion}")
    print(f"Numero de seguro: {num_seguro}")
    print(f"Hospital filiado: {hospital}")
    print(f"Numero de reporte: {num_reporte}")
    print(f"Fecha y hora del diagnostico: {fecha_diagnostico.strftime('%d/%m/%Y %H:%M:%S')}")
    
    print("\n" + "=" * 55)
    print("             INICIANDO DIAGNOSTICO")
    print("=" * 55)
    
    print(f"\n{nombre_completo}, voy a ayudarte a revisar tus sintomas.")
    print("Responde con s o n, empecemos.\n")
    
    # Listas con diferentes variantes de preguntas para cada síntoma
    preguntas_fiebre = [
        "Tiene fiebre? (s/n): ",
        "Ha presentado temperatura corporal elevada o fiebre? (s/n): ",
        "Siente que su temperatura ha subido mas de lo normal (fiebre)? (s/n): "
    ]
    preguntas_tos = [
        "Tiene tos? (s/n): ",
        "Ha estado tosiendo recientemente? (s/n): ",
        "Presenta episodios de tos? (s/n): "
    ]
    preguntas_garganta = [
        "Tiene dolor de garganta? (s/n): ",
        "Siente molestias, irritacion o dolor al tragar? (s/n): ",
        "Le duele la garganta al pasar saliva? (s/n): "
    ]
    preguntas_cabeza = [
        "Tiene dolor de cabeza? (s/n): ",
        "Siente cefalea o dolor en la cabeza? (s/n): ",
        "Le molesta la cabeza o siente presion en ella? (s/n): "
    ]
    preguntas_cansancio = [
        "Se siente cansado? (s/n): ",
        "Experimenta fatiga extrema o debilidad general? (s/n): ",
        "Siente falta de energia o cansancio inusual? (s/n): "
    ]
    preguntas_respirar = [
        "Tiene dificultad para respirar? (s/n): ",
        "Le cuesta trabajo tomar aire o respirar con normalidad? (s/n): ",
        "Siente falta de aire (disnea)? (s/n): "
    ]
    preguntas_temperatura = [
        "Tiene temperatura alta (mas de 38°C)? (s/n): ",
        "Ha registrado un termómetro con mas de 38 grados? (s/n): ",
        "Supera los 38°C de temperatura corporal? (s/n): "
    ]
    preguntas_alergias = [
        "Tiene alergias conocidas? (s/n): ",
        "Padece de alguna alergia diagnosticada previamente? (s/n): ",
        "Es usted una persona alergica a algun medicamento o sustancia? (s/n): "
    ]

    # Captura de datos usando las variantes aleatorias
    fiebre = input(obtener_pregunta(preguntas_fiebre)).strip().lower()
    tos = input(obtener_pregunta(preguntas_tos)).strip().lower()
    dolor_garganta = input(obtener_pregunta(preguntas_garganta)).strip().lower()
    dolor_cabeza = input(obtener_pregunta(preguntas_cabeza)).strip().lower()
    cansancio = input(obtener_pregunta(preguntas_cansancio)).strip().lower()
    dificultad_respirar = input(obtener_pregunta(preguntas_respirar)).strip().lower()
    temperatura = input(obtener_pregunta(preguntas_temperatura)).strip().lower()
    alergias = input(obtener_pregunta(preguntas_alergias)).strip().lower()
    
    F = fiebre == "s"
    T = tos == "s"
    D = dolor_garganta == "s"
    C = dolor_cabeza == "s"
    CAN = cansancio == "s"
    R = dificultad_respirar == "s"
    TEMP = temperatura == "s"
    AL = alergias == "s"
    
    print("\n" + "=" * 55)
    print("             VALORES DE LAS PROPOSICIONES")
    print("=" * 55)
    
    print(f"F - Fiebre                  : {F}")
    print(f"T - Tos                     : {T}")
    print(f"D - Dolor de garganta       : {D}")
    print(f"C - Dolor de cabeza         : {C}")
    print(f"CAN - Cansancio             : {CAN}")
    print(f"R - Dificultad respirar     : {R}")
    print(f"TEMP - Temperatura alta     : {TEMP}")
    print(f"AL - Alergias               : {AL}")
    print(f"RANGO - {rango_edad}")
    
    print("\n" + "-" * 55)
    print("OPERACIONES LOGICAS")
    print("-" * 55)
    
    print("\nNEGACION:")
    print(f"¬F = {not F}")
    print(f"¬T = {not T}")
    print(f"¬D = {not D}")
    
    print("\nCONJUNCION:")
    print(f"F ∧ T = {F and T}")
    print(f"D ∧ C = {D and C}")
    print(f"F ∧ R = {F and R}")
    
    print("\nDISYUNCION:")
    print(f"F ∨ T = {F or T}")
    print(f"D ∨ C = {D or C}")
    
    print("\nCONDICIONAL:")
    print(f"F → T = {(not F) or T}")
    
    print("\nBICONDICIONAL:")
    print(f"F ↔ T = {F == T}")
    
    print("\n" + "-" * 55)
    print("EXPRESIONES COMPUESTAS")
    print("-" * 55)
    
    infeccion_respiratoria = F and T and D
    gripe = F and T and C and CAN
    covid_sospecha = F and T and R
    resfriado = T and D and (not F)
    alergia = AL and (not F) and (D or T)
    
    print(f"(F ∧ T ∧ D) = {infeccion_respiratoria}")
    print(f"(F ∧ T ∧ C ∧ CAN) = {gripe}")
    print(f"(F ∧ T ∧ R) = {covid_sospecha}")
    print(f"(T ∧ D ∧ ¬F) = {resfriado}")
    print(f"(AL ∧ ¬F ∧ (D ∨ T)) = {alergia}")
    
    print("\n" + "=" * 55)
    print("                 DIAGNOSTICO")
    print("=" * 55)
    
    if rango_edad == "Bebe" and (F or TEMP):
        print("DIAGNOSTICO: Fiebre en bebe - REQUIERE ATENCION INMEDIATA")
        print("Recomendacion: Acudir a urgencias pediatricas de inmediato")
        print("")
        print("Sintomas detectados:")
        if F:
            print("- Fiebre")
        if TEMP:
            print("- Temperatura alta")
        print("")
        print("ADVERTENCIA: Los bebes con fiebre requieren evaluacion inmediata")
        print("Nivel de gravedad: URGENTE")
        num_diagnostico = 401
        
    elif rango_edad == "Bebe" and (T or R):
        print("DIAGNOSTICO: Problema respiratorio en bebe - REQUIERE ATENCION")
        print("Recomendacion: Acudir a urgencias pediatricas")
        print("")
        print("Sintomas detectados:")
        if T:
            print("- Tos")
        if R:
            print("- Dificultad para respirar")
        print("")
        print("ADVERTENCIA: Problemas respiratorios en bebes son graves")
        print("Nivel de gravedad: URGENTE")
        num_diagnostico = 402
    
    elif rango_edad == "Adulto mayor" and F and T and R:
        print("DIAGNOSTICO: Infeccion respiratoria grave en adulto mayor")
        print("Recomendacion: Acudir a urgencias de inmediato")
        print("")
        print("Sintomas detectados:")
        print("- Fiebre")
        print("- Tos")
        print("- Dificultad para respirar")
        print("")
        print("ADVERTENCIA: Adultos mayores son grupo de riesgo")
        print("Nivel de gravedad: ALTO")
        num_diagnostico = 403
        
    elif rango_edad == "Adulto mayor" and F:
        print("DIAGNOSTICO: Fiebre en adulto mayor")
        print("Recomendacion: Consultar con medico general")
        print("")
        print("Sintomas detectados:")
        print("- Fiebre")
        print("")
        print("ADVERTENCIA: Adultos mayores requieren monitoreo constante")
        print("Nivel de gravedad: MEDIO")
        num_diagnostico = 404
    
    elif rango_edad == "Niño" and F and T and R:
        print("DIAGNOSTICO: Infeccion respiratoria en niño")
        print("Recomendacion: Acudir a pediatra")
        print("")
        print("Sintomas detectados:")
        print("- Fiebre")
        print("- Tos")
        print("- Dificultad para respirar")
        print("")
        print("Nivel de gravedad: ALTO")
        num_diagnostico = 405
        
    elif rango_edad == "Niño" and T and D and (not F):
        print("DIAGNOSTICO: Resfriado comun en niño")
        print("Recomendacion: Reposo y liquidos")
        print("")
        print("Sintomas detectados:")
        print("- Tos")
        print("- Dolor de garganta")
        print("- Sin fiebre")
        print("")
        print("Nivel de gravedad: BAJO")
        num_diagnostico = 406
    
    elif F and T and R:
        print("DIAGNOSTICO: Posible infeccion respiratoria grave")
        print("Recomendacion: Acudir a urgencias de inmediato")
        print("")
        print("Sintomas detectados:")
        print("- Fiebre")
        print("- Tos")
        print("- Dificultad para respirar")
        print("")
        print("Nivel de gravedad: ALTO")
        num_diagnostico = 301
        
    elif F and T and D:
        print("DIAGNOSTICO: Posible infeccion respiratoria")
        print("Recomendacion: Consultar con medico general")
        print("")
        print("Sintomas detectados:")
        print("- Fiebre")
        print("- Tos")
        print("- Dolor de garganta")
        print("")
        print("Nivel de gravedad: MEDIO")
        num_diagnostico = 302
        
    elif F and T and C and CAN:
        print("DIAGNOSTICO: Posible gripe")
        print("Recomendacion: Reposo y medicamentos para la fiebre")
        print("")
        print("Sintomas detectados:")
        print("- Fiebre")
        print("- Tos")
        print("- Dolor de cabeza")
        print("- Cansancio")
        print("")
        print("Nivel de gravedad: MEDIO")
        num_diagnostico = 303
        
    elif T and D and (not F):
        print("DIAGNOSTICO: Posible resfriado comun")
        print("Recomendacion: Reposo y tomar liquidos")
        print("")
        print("Sintomas detectados:")
        print("- Tos")
        print("- Dolor de garganta")
        print("- Sin fiebre")
        print("")
        print("Nivel de gravedad: BAJO")
        num_diagnostico = 304
        
    elif AL and (not F) and (D or T):
        print("DIAGNOSTICO: Posible reaccion alergica")
        print("Recomendacion: Evitar alergenos y consultar con alergologo")
        print("")
        print("Sintomas detectados:")
        print("- Alergias conocidas")
        if D:
            print("- Dolor de garganta")
        if T:
            print("- Tos")
        print("- Sin fiebre")
        print("")
        print("Nivel de gravedad: BAJO")
        num_diagnostico = 307
        
    elif F and (not T) and (not D):
        print("DIAGNOSTICO: Fiebre sin otros sintomas")
        print("Recomendacion: Monitorear temperatura y consultar si persiste")
        print("")
        print("Sintomas detectados:")
        print("- Fiebre")
        print("")
        print("Nivel de gravedad: BAJO")
        num_diagnostico = 305
        
    elif F and D and (not T):
        print("DIAGNOSTICO: Posible faringitis")
        print("Recomendacion: Consultar con medico para antibioticos si es necesario")
        print("")
        print("Sintomas detectados:")
        print("- Fiebre")
        print("- Dolor de garganta")
        print("")
        print("Nivel de gravedad: MEDIO")
        num_diagnostico = 306
        
    else:
        print("DIAGNOSTICO: No se identifico un patron claro")
        print("Recomendacion: Consultar con medico para evaluacion completa")
        print("")
        print("Sintomas detectados:")
        if F:
            print("- Fiebre")
        if T:
            print("- Tos")
        if D:
            print("- Dolor de garganta")
        if C:
            print("- Dolor de cabeza")
        if CAN:
            print("- Cansancio")
        if R:
            print("- Dificultad para respirar")
        if TEMP:
            print("- Temperatura alta")
        if AL:
            print("- Alergias")
        if not F and not T and not D and not C and not CAN and not R and not TEMP and not AL:
            print("- Ningun sintoma reportado")
        print("")
        print("Nivel de gravedad: BAJO")
        num_diagnostico = 300
    
    print("\n" + "=" * 55)
    print("                 RESULTADO FINAL")
    print("=" * 55)
    
    print(f"PACIENTE: {nombre_completo}")
    print(f"EDAD: {edad} años ({rango_edad})")
    print(f"HOSPITAL: {hospital}")
    print(f"REPORTE: {num_reporte}")
    print(f"DIAGNOSTICO: {num_diagnostico}")
    
    print("\n" + "=" * 55)
    print("             RECOMENDACIONES POR EDAD")
    print("=" * 55)
    
    if rango_edad == "Bebe":
        print("- ATENCION URGENTE: Acudir al pediatra de inmediato")
        print("- No automedicar al bebe")
        print("- Mantenerlo hidratado con leche materna o formula")
        print("- Monitorear temperatura constantemente")
        
    elif rango_edad == "Niño":
        print("- Consultar con pediatra")
        print("- Reposo en casa")
        print("- No enviar a la escuela hasta recuperarse")
        print("- Mantenerlo hidratado")
        
    elif rango_edad == "Adolescente":
        print("- Reposo adecuado")
        print("- Evitar actividades fisicas intensas")
        print("- Mantenerse hidratado")
        print("- Consultar si los sintomas persisten")
        
    elif rango_edad == "Adulto":
        print("- Reposo en casa")
        print("- Tomar medicamentos segun indicacion")
        print("- Mantenerse hidratado")
        print("- No automedicarse")
        
    elif rango_edad == "Adulto mayor":
        print("- ATENCION: Grupo de riesgo, monitoreo constante")
        print("- Acudir al medico a la brevedad")
        print("- Mantenerse hidratado")
        print("- No automedicar")
    
    print("\n" + "=" * 55)
    print("             RECOMENDACIONES GENERALES")
    print("=" * 55)
    
    print("- Mantenerse hidratado")
    print("- Reposo adecuado")
    print("- Tomar temperatura regularmente")
    if F or TEMP:
        print("- Tomar paracetamol para la fiebre (consultar dosis por edad)")
    if T:
        print("- Usar miel y limon para la tos (excepto en bebes)")
        if rango_edad == "Bebe":
            print("- NO dar miel a bebes menores de 1 año")
    if D:
        print("- Hacer gargaras con agua y sal (excepto en niños pequeños)")
    print("- Acudir al medico si los sintomas empeoran")
    
    print("\n" + "=" * 55)
    print("             INFORMACION DEL DIAGNOSTICO")
    print("=" * 55)
    
    print(f"Paciente: {nombre_completo}")
    print(f"Edad: {edad} años ({rango_edad})")
    print(f"Direccion: {direccion}")
    print(f"Seguro social: {num_seguro}")
    print(f"Hospital: {hospital}")
    print(f"Reporte: {num_reporte}")
    print(f"Diagnostico: {num_diagnostico}")
    print(f"Fecha y hora: {fecha_diagnostico.strftime('%d/%m/%Y %H:%M:%S')}")
    
    print("\n" + "=" * 55)
    print("             RESUMEN DEL DIAGNOSTICO")
    print("=" * 55)
    
    print("\nDATOS DEL PACIENTE:")
    print(f"Nombre: {nombre_completo}")
    print(f"Edad: {edad} años ({rango_edad})")
    print(f"Direccion: {direccion}")
    print(f"Hospital: {hospital}")
    print(f"Reporte: {num_reporte}")
    
    print("\nSINTOMAS REPORTADOS:")
    print(f"Fiebre: {'SI' if F else 'NO'}")
    print(f"Tos: {'SI' if T else 'NO'}")
    print(f"Dolor de garganta: {'SI' if D else 'NO'}")
    print(f"Dolor de cabeza: {'SI' if C else 'NO'}")
    print(f"Cansancio: {'SI' if CAN else 'NO'}")
    print(f"Dificultad para respirar: {'SI' if R else 'NO'}")
    print(f"Temperatura alta: {'SI' if TEMP else 'NO'}")
    print(f"Alergias: {'SI' if AL else 'NO'}")
    
    print("\nRESULTADO:")
    print(f"Diagnostico: {num_diagnostico}")
    print(f"Rango de edad: {rango_edad}")
    
    print("\n" + "=" * 55)
    print("                 FIN DEL DIAGNOSTICO")
    print("=" * 55)

def mostrar_menu():
    print("\n" + "=" * 55)
    print("                 MENU PRINCIPAL")
    print("=" * 55)
    print("1. Realizar nuevo diagnostico")
    print("2. Salir del sistema")
    print("=" * 55)

while True:
    mostrar_menu()
    opcion = input("\nSelecciona una opcion (1-2): ")
    
    if opcion == "1":
        realizar_diagnostico()
        
        while True:
            print("\n" + "=" * 55)
            print("             CONTINUAR?")
            print("=" * 55)
            continuar = input("Quieres hacer otro diagnostico? (si/no): ").strip().lower()
            
            if continuar == "si":
                print("\nContinuando con un nuevo diagnostico...")
                realizar_diagnostico()
            elif continuar == "no":
                fecha_fin = datetime.datetime.now(mexico_tz)
                print("\n" + "=" * 55)
                print("        GRACIAS POR USAR EL SISTEMA")
                print("=" * 55)
                print(f"Total de reportes generados: {contador_reportes}")
                print(f"Fecha y hora de inicio: {fecha_inicio.strftime('%d/%m/%Y %H:%M:%S')}")
                print(f"Fecha y hora de finalizacion: {fecha_fin.strftime('%d/%m/%Y %H:%M:%S')}")
                print("Hasta luego!")
                exit()
            else:
                print("\nRespuesta no valida, por favor responde 'si' o 'no'.")
                continue
            
    elif opcion == "2":
        fecha_fin = datetime.datetime.now(mexico_tz)
        print("\n" + "=" * 55)
        print("        GRACIAS POR USAR EL SISTEMA")
        print("=" * 55)
        print(f"Total de reportes generados: {contador_reportes}")
        print(f"Fecha y hora de inicio: {fecha_inicio.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Fecha y hora de finalizacion: {fecha_fin.strftime('%d/%m/%Y %H:%M:%S')}")
        print("Hasta luego!")
        break
        
    else:
        print("\nOpcion no valida, intenta de nuevo.")

print("\n" + "=" * 55)
print("        SISTEMA FINALIZADO")
print("=" * 55)