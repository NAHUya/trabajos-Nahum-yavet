print("TABLA DE VERDAD")
print("=" * 75)

print("A\tB\tAND\tOR\tNOT A\tXOR\tA -> B\tA <-> B")
print("-" * 75)

A = False
B = False

if A and B:
    AND = True
else:
    AND = False

if A or B:
    OR = True
else:
    OR = False

if A:
    NOT_A = False
else:
    NOT_A = True

if A != B:
    XOR = True
else:
    XOR = False

if A == True and B == False:
    IMP = False
else:
    IMP = True

if A == B:
    BIC = True
else:
    BIC = False

print(f"{'V' if A else 'F'}\t{'V' if B else 'F'}\t"
      f"{'V' if AND else 'F'}\t{'V' if OR else 'F'}\t"
      f"{'V' if NOT_A else 'F'}\t{'V' if XOR else 'F'}\t"
      f"{'V' if IMP else 'F'}\t{'V' if BIC else 'F'}")

A = False
B = True

if A and B:
    AND = True
else:
    AND = False

if A or B:
    OR = True
else:
    OR = False

if A:
    NOT_A = False
else:
    NOT_A = True

if A != B:
    XOR = True
else:
    XOR = False

if A == True and B == False:
    IMP = False
else:
    IMP = True

if A == B:
    BIC = True
else:
    BIC = False

print(f"{'V' if A else 'F'}\t{'V' if B else 'F'}\t"
      f"{'V' if AND else 'F'}\t{'V' if OR else 'F'}\t"
      f"{'V' if NOT_A else 'F'}\t{'V' if XOR else 'F'}\t"
      f"{'V' if IMP else 'F'}\t{'V' if BIC else 'F'}")

A = True
B = False

if A and B:
    AND = True
else:
    AND = False

if A or B:
    OR = True
else:
    OR = False

if A:
    NOT_A = False
else:
    NOT_A = True

if A != B:
    XOR = True
else:
    XOR = False

if A == True and B == False:
    IMP = False
else:
    IMP = True

if A == B:
    BIC = True
else:
    BIC = False

print(f"{'V' if A else 'F'}\t{'V' if B else 'F'}\t"
      f"{'V' if AND else 'F'}\t{'V' if OR else 'F'}\t"
      f"{'V' if NOT_A else 'F'}\t{'V' if XOR else 'F'}\t"
      f"{'V' if IMP else 'F'}\t{'V' if BIC else 'F'}")

A = True
B = True

if A and B:
    AND = True
else:
    AND = False

if A or B:
    OR = True
else:
    OR = False

if A:
    NOT_A = False
else:
    NOT_A = True

if A != B:
    XOR = True
else:
    XOR = False

if A == True and B == False:
    IMP = False
else:
    IMP = True

if A == B:
    BIC = True
else:
    BIC = False

print(f"{'V' if A else 'F'}\t{'V' if B else 'F'}\t"
      f"{'V' if AND else 'F'}\t{'V' if OR else 'F'}\t"
      f"{'V' if NOT_A else 'F'}\t{'V' if XOR else 'F'}\t"
      f"{'V' if IMP else 'F'}\t{'V' if BIC else 'F'}")