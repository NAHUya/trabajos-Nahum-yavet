print("=" * 55)
print("        CONTROL DE INGRESO A EVALUACIÓN")
print("=" * 55)

porcentaje = float(
    input("Escribe el porcentaje de asistencia: ")
)

calificacion = float(
    input("Escribe la calificación obtenida: ")
)

trabajo_final = input(
    "¿Presentó el trabajo final? (si/no): "
).lower()

pendientes = input(
    "¿Cuenta con materias pendientes? (si/no): "
).lower()

permiso = input(
    "¿Cuenta con un permiso especial? (si/no): "
).lower()

registro_examen = input(
    "¿Está registrado para el examen? (si/no): "
).lower()

# A: El estudiante cumple con la asistencia mínima
A = porcentaje >= 80

# B: El estudiante obtiene una calificación aprobatoria
B = calificacion >= 8

# C: El estudiante presentó el trabajo final
C = trabajo_final == "si"

# D: El estudiante no tiene materias pendientes
D = pendientes == "no"

# E: El estudiante cuenta con un permiso especial
E = permiso == "si"

# F: El estudiante está registrado para presentar el examen
F = registro_examen == "si"

print("\n" + "=" * 55)
print("             ESTADO DE LAS CONDICIONES")
print("=" * 55)

print("A - Asistencia mínima       :", A)
print("B - Calificación aprobatoria:", B)
print("C - Trabajo final entregado :", C)
print("D - Sin materias pendientes :", D)
print("E - Permiso especial        :", E)
print("F - Registro para examen    :", F)

negacion_A = not A

print("\nNEGACIÓN")
print("¬A =", negacion_A)

resultado_and = A and B

print("\nCONJUNCIÓN")
print("A ∧ B =", resultado_and)

resultado_or = B or E

print("\nDISYUNCIÓN")
print("B ∨ E =", resultado_or)

resultado_condicional = (not A) or B

print("\nCONDICIONAL")
print("A → B =", resultado_condicional)

resultado_bicondicional = A == B

print("\nBICONDICIONAL")
print("A ↔ B =", resultado_bicondicional)

acceso = ((A and B and C and D) or E) and F

print("\nREGLA DE ACCESO")
print("((A ∧ B ∧ C ∧ D) ∨ E) ∧ F =", acceso)

coincidencia = E == F

print("\nCOMPARACIÓN DE AUTORIZACIÓN")
print("E ↔ F =", coincidencia)

print("\n" + "=" * 55)
print("                 ESTADO FINAL")
print("=" * 55)

if acceso:
    print("El estudiante está AUTORIZADO para presentar la evaluación.")
else:
    print("El estudiante NO está autorizado para presentar la evaluación.")

if coincidencia:
    print("El permiso y el registro presentan valores coincidentes.")
else:
    print("AVISO: El permiso y el registro presentan valores diferentes.")