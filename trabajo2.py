print("==============================================")
print("       CONTROL DE ACCESO AL EXAMEN")
print("==============================================")

asistencia = float(
    input("Ingresa el porcentaje de asistencia: ")
)

calificacion = float(
    input("Ingresa la calificación final: ")
)

trabajo = input(
    "¿Entregó el trabajo final? (si/no): "
).lower()

permiso = input(
    "¿Cuenta con un permiso especial? (si/no): "
).lower()

materias_pendientes = input(
    "¿Tiene materias pendientes? (si/no): "
).lower()

registro = input(
    "¿Está registrado en la lista del examen? (si/no): "
).lower()


# A es verdadera cuando la asistencia es de 80% o más
A = asistencia >= 80

# B es verdadera cuando la calificación es de 7 o más
B = calificacion >= 7

# C es verdadera cuando entregó el trabajo final
C = trabajo == "si"

# D es verdadera cuando cuenta con un permiso especial
D = permiso == "si"

# E es verdadera cuando NO tiene materias pendientes
E = materias_pendientes == "no"

# F es verdadera cuando está registrado en la lista
F = registro == "si"


print("\n==============================================")
print("          VALORES DE LAS PROPOSICIONES")
print("==============================================")

print("A - Asistencia requerida:", A)
print("B - Calificación aprobatoria:", B)
print("C - Trabajo entregado:", C)
print("D - Permiso especial:", D)
print("E - Sin materias pendientes:", E)
print("F - Registrado en la lista:", F)


# Negaciones
neg_A = not A
neg_E = not E
neg_F = not F

print("\n==============================================")
print("                  NEGACIÓN")
print("==============================================")

print("¬A =", neg_A)


# Conjunción
union = A and B

print("\n==============================================")
print("                CONJUNCIÓN")
print("==============================================")

print("A ∧ B =", union)


# Disyunción
alternativa = B or D

print("\n==============================================")
print("                 DISYUNCIÓN")
print("==============================================")

print("B ∨ D =", alternativa)


# Condicional
condicional = (not A) or B

print("\n==============================================")
print("                 CONDICIONAL")
print("==============================================")

print("A → B =", condicional)


# Bicondicional
equivalencia = A == B

print("\n==============================================")
print("               BICONDICIONAL")
print("==============================================")

print("A ↔ B =", equivalencia)


# Expresión lógica completa
resultado_final = ((A and B) or D) and ((not E) or D) and F

print("\n==============================================")
print("             EXPRESIÓN LÓGICA")
print("==============================================")

print("((A ∧ B) ∨ D) ∧ (¬E ∨ D) ∧ F =", resultado_final)


# Resultado
if resultado_final:

    print("\nRESULTADO:")
    print("El estudiante está AUTORIZADO para realizar el examen.")

else:

    print("\nRESULTADO:")
    print("El estudiante NO está autorizado para realizar el examen.")

    if E and not D:
        print("MOTIVO: El estudiante tiene materias pendientes")
        print("        y no cuenta con un permiso especial.")

    if not F:
        print("MOTIVO: El estudiante no está registrado")
        print("        en la lista del examen.")