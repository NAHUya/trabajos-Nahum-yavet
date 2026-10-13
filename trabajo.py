"""Aplicación unificada de control de acceso, incidentes y riesgos éticos.

Este archivo reúne en un único script la lógica de negocio, persistencia local,
clasificación por reglas + LLM y la interfaz Tkinter."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from typing import Any
from uuid import uuid4

import httpx
import ollama
import tkinter as tk
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError


MODELO_DEFAULT = "llama3.2"


def normalizar_bool(valor: Any, predeterminado: bool = False) -> bool:
    """Normaliza valores booleanos que pueden venir como texto o enteros."""
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return bool(valor)
    if isinstance(valor, str):
        texto = valor.strip().casefold()
        if not texto:
            return predeterminado
        if texto in {"1", "true", "yes", "y", "on"}:
            return True
        if texto in {"0", "false", "no", "n", "off"}:
            return False
    return bool(valor) if valor is not None else predeterminado


def identificador() -> str:
    return str(uuid4())


def evaluar_acceso(
    p: bool | None = None,
    q: bool | None = None,
    r: bool | None = None,
    s: bool | None = None,
    *,
    P: bool | None = None,
    Q: bool | None = None,
    R: bool | None = None,
    S: bool | None = None,
    certificacion_vigente: bool = True,
    materiales_peligrosos: bool = False,
    horario_permitido: bool = True,
) -> dict[str, Any]:
    """Evalúa las reglas lógicas y devuelve decisión con explicación."""
    if p is None:
        p = P
    if q is None:
        q = Q
    if r is None:
        r = R
    if s is None:
        s = S

    p = normalizar_bool(p)
    q = normalizar_bool(q)
    r = normalizar_bool(r)
    s = normalizar_bool(s)
    certificacion_vigente = normalizar_bool(certificacion_vigente, True)
    materiales_peligrosos = normalizar_bool(materiales_peligrosos)
    horario_permitido = normalizar_bool(horario_permitido, True)

    acceso_base = p and s and not q
    inspeccion_base = p and (r or q)
    certificacion_bloquea = not certificacion_vigente
    inspeccion_horario = materiales_peligrosos and not horario_permitido
    acceso_autorizado = acceso_base and certificacion_vigente and not inspeccion_horario
    requiere_inspeccion = inspeccion_base or inspeccion_horario

    explicacion = [
        f"A = P ∧ S ∧ ¬Q = {p} ∧ {s} ∧ ¬{q} = {acceso_base}.",
        f"E = P ∧ (R ∨ Q) = {p} ∧ ({r} ∨ {q}) = {inspeccion_base}.",
    ]
    if certificacion_bloquea:
        explicacion.append("Regla adicional 1: certificación vencida; se bloquea la autorización.")
    if inspeccion_horario:
        explicacion.append(
            "Regla adicional 2: material peligroso fuera del horario permitido; "
            "se requiere inspección y no hay acceso automático."
        )
    if acceso_autorizado:
        explicacion.append("Resultado final: acceso autorizado por las reglas.")
    elif requiere_inspeccion:
        explicacion.append("Resultado final: detener en zona segura y solicitar revisión humana.")
    else:
        explicacion.append("Resultado final: acceso no autorizado por las reglas.")

    return {
        "A": acceso_base,
        "E": inspeccion_base,
        "bloqueo_certificacion": certificacion_bloquea,
        "bloqueo_horario": inspeccion_horario,
        "acceso_autorizado": acceso_autorizado,
        "requiere_inspeccion": requiere_inspeccion,
        "A_final": acceso_autorizado,
        "E_final": requiere_inspeccion,
        "certificacion_bloquea": certificacion_bloquea,
        "inspeccion_horario": inspeccion_horario,
        "explicacion": explicacion,
    }


def crear_acceso(datos: dict[str, Any], operador: str) -> dict[str, Any]:
    resultado = evaluar_acceso(
        normalizar_bool(datos["P"]),
        normalizar_bool(datos["Q"]),
        normalizar_bool(datos["R"]),
        normalizar_bool(datos["S"]),
        certificacion_vigente=normalizar_bool(datos.get("certificacion_vigente", True), True),
        materiales_peligrosos=normalizar_bool(datos.get("materiales_peligrosos", False)),
        horario_permitido=normalizar_bool(datos.get("horario_permitido", True), True),
    )
    return {
        "_id": identificador(),
        "placa": str(datos.get("placa", "")).strip().upper(),
        "P": normalizar_bool(datos["P"]),
        "Q": normalizar_bool(datos["Q"]),
        "R": normalizar_bool(datos["R"]),
        "S": normalizar_bool(datos["S"]),
        **resultado,
        "operador": (operador or "operador").strip() or "operador",
        "fecha": datetime.now(timezone.utc).isoformat(),
    }


def generar_tabla_verdad() -> list[dict[str, Any]]:
    filas: list[dict[str, Any]] = []
    for p in (False, True):
        for q in (False, True):
            for r in (False, True):
                for s in (False, True):
                    resultado = evaluar_acceso(p, q, r, s)
                    filas.append(
                        {
                            "P": p,
                            "Q": q,
                            "R": r,
                            "S": s,
                            "A": resultado["A"],
                            "E": resultado["E"],
                        }
                    )
    return filas


def generar_tabla_verdad_extendida() -> list[dict[str, Any]]:
    filas: list[dict[str, Any]] = []
    for p in (False, True):
        for q in (False, True):
            for r in (False, True):
                for s in (False, True):
                    for certificacion_vigente in (False, True):
                        for materiales_peligrosos in (False, True):
                            for horario_permitido in (False, True):
                                resultado = evaluar_acceso(
                                    p,
                                    q,
                                    r,
                                    s,
                                    certificacion_vigente=certificacion_vigente,
                                    materiales_peligrosos=materiales_peligrosos,
                                    horario_permitido=horario_permitido,
                                )
                                filas.append(
                                    {
                                        "P": p,
                                        "Q": q,
                                        "R": r,
                                        "S": s,
                                        "V": certificacion_vigente,
                                        "H": materiales_peligrosos,
                                        "T": horario_permitido,
                                        "A": resultado["A"],
                                        "E": resultado["E"],
                                        "bloqueo_certificacion": resultado["bloqueo_certificacion"],
                                        "bloqueo_horario": resultado["bloqueo_horario"],
                                        "A_final": resultado["A_final"],
                                        "E_final": resultado["E_final"],
                                    }
                                )
    return filas


def riesgo_nuevo(datos: dict[str, Any]) -> dict[str, Any]:
    probabilidad = int(datos["probabilidad"])
    impacto = int(datos["impacto"])
    prob_residual = int(datos.get("probabilidad_residual", probabilidad))
    impacto_residual = int(datos.get("impacto_residual", impacto))
    ahora = datetime.now(timezone.utc).isoformat()
    return {
        "_id": str(datos.get("_id") or identificador()),
        "modulo": str(datos["modulo"]).strip(),
        "descripcion": str(datos["descripcion"]).strip(),
        "categoria": str(datos["categoria"]).strip(),
        "probabilidad": probabilidad,
        "impacto": impacto,
        "mitigacion": str(datos["mitigacion"]).strip(),
        "probabilidad_residual": prob_residual,
        "impacto_residual": impacto_residual,
        "puntaje": probabilidad * impacto,
        "puntaje_residual": prob_residual * impacto_residual,
        "fecha": ahora,
        "historial": [{
            "accion": "creado",
            "fecha": ahora,
            "probabilidad": probabilidad,
            "impacto": impacto,
            "mitigacion": str(datos["mitigacion"]).strip(),
            "probabilidad_residual": prob_residual,
            "impacto_residual": impacto_residual,
        }],
    }


def incidente_nuevo(correo: str, clasificacion: dict[str, Any]) -> dict[str, Any]:
    ahora = datetime.now(timezone.utc).isoformat()
    return {
        "_id": identificador(),
        "correo_original": correo.strip(),
        **clasificacion,
        "estado": "nuevo",
        "fecha": ahora,
        "historial": [{"estado": "nuevo", "fecha": ahora}],
    }


COLECCIONES = ("camiones", "accesos", "incidentes", "riesgos_eticos", "evaluaciones_llm")


def datos_demostracion() -> dict[str, list[dict[str, Any]]]:
    return {
        "camiones": [
            {
                "_id": "CAM-101",
                "placa": "ABC-123",
                "camion_id": "CAM-101",
                "empresa": "Transporte del Norte",
                "autorizacion": True,
                "certificacion_conductor": "2027-12-31",
                "materiales_peligrosos": False,
            },
            {
                "_id": "CAM-102",
                "placa": "XYZ-789",
                "camion_id": "CAM-102",
                "empresa": "Logística Segura",
                "autorizacion": True,
                "certificacion_conductor": "2024-05-01",
                "materiales_peligrosos": True,
            },
        ],
        "accesos": [],
        "incidentes": [{
            "_id": "INC-DEMO-1",
            "correo_original": "El conductor reporta una demora y solicita confirmar la documentación de entrada.",
            "categoria": "documentacion",
            "prioridad": "media",
            "entidades": {"placas": [], "camiones": [], "personas": []},
            "resumen": "Consulta de documentación de entrada.",
            "estado": "nuevo",
            "fecha": datetime.now(timezone.utc).isoformat(),
            "historial": [],
        }],
        "riesgos_eticos": [
            {
                "_id": "RIESGO-1",
                "modulo": "Clasificador LLM",
                "descripcion": "El modelo puede producir una clasificación incorrecta.",
                "categoria": "alucinación",
                "probabilidad": 3,
                "impacto": 5,
                "mitigacion": "Reglas de respaldo y revisión humana obligatoria.",
                "probabilidad_residual": 2,
                "impacto_residual": 3,
                "puntaje": 15,
                "puntaje_residual": 6,
                "fecha": datetime.now(timezone.utc).isoformat(),
            },
            {
                "_id": "RIESGO-2",
                "modulo": "Clasificador de correos",
                "descripcion": "La ortografía informal puede perjudicar la clasificación.",
                "categoria": "sesgo",
                "probabilidad": 3,
                "impacto": 4,
                "mitigacion": "Medir por estilo lingüístico y permitir corrección.",
                "probabilidad_residual": 2,
                "impacto_residual": 3,
                "puntaje": 12,
                "puntaje_residual": 6,
                "fecha": datetime.now(timezone.utc).isoformat(),
            },
        ],
        "evaluaciones_llm": [],
    }


class Repositorio:
    def __init__(self, archivo: Path | None = None) -> None:
        self._lock = threading.RLock()
        ruta_base = Path(__file__).resolve().parent
        self.archivo = archivo or (ruta_base / "data" / "logistica.json")
        self.archivo.parent.mkdir(parents=True, exist_ok=True)
        if not self.archivo.exists():
            self._escribir(datos_demostracion())
        self.modo = f"Archivo local: {self.archivo}"
        self._asegurar_colecciones()

    def _leer(self) -> dict[str, list[dict[str, Any]]]:
        with self.archivo.open("r", encoding="utf-8") as archivo:
            return json.load(archivo)

    def _escribir(self, datos: dict[str, list[dict[str, Any]]]) -> None:
        self.archivo.parent.mkdir(parents=True, exist_ok=True)
        temporal: Path | None = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.archivo.parent, delete=False) as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
                temporal = Path(archivo.name)
            temporal.replace(self.archivo)
        finally:
            if temporal is not None and temporal.exists():
                temporal.unlink()

    def _asegurar_colecciones(self) -> None:
        datos = self._leer()
        cambios = False
        for coleccion in COLECCIONES:
            if coleccion not in datos:
                datos[coleccion] = []
                cambios = True
        for riesgo in datos.get("riesgos_eticos", []):
            if not riesgo.get("historial"):
                riesgo["historial"] = [{
                    "accion": "registrado",
                    "fecha": riesgo.get("fecha", datetime.now(timezone.utc).isoformat()),
                    "modulo": riesgo.get("modulo", ""),
                    "descripcion": riesgo.get("descripcion", ""),
                    "categoria": riesgo.get("categoria", ""),
                    "probabilidad": riesgo.get("probabilidad"),
                    "impacto": riesgo.get("impacto"),
                    "mitigacion": riesgo.get("mitigacion", ""),
                    "probabilidad_residual": riesgo.get("probabilidad_residual"),
                    "impacto_residual": riesgo.get("impacto_residual"),
                    "puntaje": riesgo.get("puntaje"),
                    "puntaje_residual": riesgo.get("puntaje_residual"),
                }]
                cambios = True
        if cambios:
            self._escribir(datos)

    def listar(self, coleccion: str) -> list[dict[str, Any]]:
        self._validar_coleccion(coleccion)
        with self._lock:
            return list(self._leer().get(coleccion, []))

    def obtener(self, coleccion: str, identificador_: str) -> dict[str, Any] | None:
        return next(
            (documento for documento in self.listar(coleccion) if str(documento.get("_id")) == str(identificador_)),
            None,
        )

    def guardar(self, coleccion: str, documento: dict[str, Any]) -> dict[str, Any]:
        self._validar_coleccion(coleccion)
        guardado = dict(documento)
        guardado.setdefault("_id", str(os.urandom(12).hex()))
        with self._lock:
            datos = self._leer()
            existentes = datos.setdefault(coleccion, [])
            for indice, actual in enumerate(existentes):
                if str(actual.get("_id")) == str(guardado["_id"]):
                    existentes[indice] = guardado
                    break
            else:
                existentes.append(guardado)
            self._escribir(datos)
        return guardado

    def eliminar(self, coleccion: str, identificador_: str) -> bool:
        self._validar_coleccion(coleccion)
        with self._lock:
            datos = self._leer()
            anteriores = datos.get(coleccion, [])
            nuevos = [documento for documento in anteriores if str(documento.get("_id")) != str(identificador_)]
            if len(nuevos) == len(anteriores):
                return False
            datos[coleccion] = nuevos
            self._escribir(datos)
            return True

    def incidentes_por_categoria_semana(self) -> list[dict[str, Any]]:
        conteo: Counter[tuple[str, int, int]] = Counter()
        for incidente in self.listar("incidentes"):
            try:
                fecha = datetime.fromisoformat(str(incidente.get("fecha", "")).replace("Z", "+00:00"))
                anio, semana, _ = fecha.isocalendar()
                categoria = str(incidente.get("categoria", "sin_categoria"))
                conteo[(categoria, anio, semana)] += 1
            except (TypeError, ValueError):
                continue
        return [{
            "categoria": categoria,
            "anio": anio,
            "semana": semana,
            "total": total,
        } for (categoria, anio, semana), total in sorted(conteo.items())]

    @staticmethod
    def _validar_coleccion(coleccion: str) -> None:
        if coleccion not in COLECCIONES:
            raise ValueError(f"Colección desconocida: {coleccion}.")


class Entidades(BaseModel):
    model_config = ConfigDict(extra="forbid")
    placas: list[str] = Field(default_factory=list)
    camiones: list[str] = Field(default_factory=list)
    personas: list[str] = Field(default_factory=list)


class Categoria(str, Enum):
    seguridad = "seguridad"
    documentacion = "documentacion"
    operativo = "operativo"
    acceso = "acceso"
    otro = "otro"


class Prioridad(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"
    critica = "critica"


class Clasificacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    categoria: Categoria
    prioridad: Prioridad
    entidades: Entidades
    resumen: str = Field(min_length=1, max_length=500)

    def como_documento(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


PESOS_CATEGORIA = {
    "seguridad": ("robo", "amenaza", "accidente", "arma", "derrame"),
    "documentacion": ("certificacion", "documentacion", "documento", "papel", "licencia", "permiso"),
    "operativo": ("demora", "retraso", "carga", "descarga", "falla"),
    "acceso": ("acceso", "entrada", "porton", "autorizacion", "ingreso"),
}
PALABRAS_CRITICAS = ("arma", "amenaza", "derrame", "herido", "incendio", "robo")
PALABRAS_ALTAS = ("accidente", "fuga", "vencida", "vencido", "sin permiso")
ORDEN_PRIORIDAD = {Prioridad.baja: 1, Prioridad.media: 2, Prioridad.alta: 3, Prioridad.critica: 4}


def clasificar_por_reglas(correo: str) -> Clasificacion:
    normalizado = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", correo.casefold())
        if not unicodedata.combining(caracter)
    )
    categoria = Categoria.otro
    coincidencias = {nombre: sum(palabra in normalizado for palabra in palabras) for nombre, palabras in PESOS_CATEGORIA.items()}
    if max(coincidencias.values(), default=0):
        categoria = Categoria(max(coincidencias, key=coincidencias.get))

    if any(palabra in normalizado for palabra in PALABRAS_CRITICAS):
        prioridad = Prioridad.critica
    elif any(palabra in normalizado for palabra in PALABRAS_ALTAS):
        prioridad = Prioridad.alta
    elif categoria is Categoria.otro:
        prioridad = Prioridad.baja
    else:
        prioridad = Prioridad.media

    return Clasificacion(
        categoria=categoria,
        prioridad=prioridad,
        entidades=Entidades(
            placas=list(dict.fromkeys(re.findall(r"\b[A-Z]{2,4}[- ]?\d{2,4}\b", correo.upper()))),
            camiones=list(dict.fromkeys(re.findall(r"\bCAM[- ]?\d{2,6}\b", correo.upper()))),
            personas=[],
        ),
        resumen="Clasificación de respaldo basada en palabras clave.",
    )


def _anonimizar(correo: str) -> str:
    correo = re.sub(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "[CORREO REDACTADO]",
        correo,
        flags=re.IGNORECASE,
    )
    return re.sub(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)", "[TELÉFONO REDACTADO]", correo)


def fusionar_clasificaciones(resultado_llm: Clasificacion, resultado_reglas: Clasificacion) -> tuple[Clasificacion, bool]:
    coincide = resultado_llm.categoria == resultado_reglas.categoria and resultado_llm.prioridad == resultado_reglas.prioridad
    prioridad = max((resultado_llm.prioridad, resultado_reglas.prioridad), key=ORDEN_PRIORIDAD.__getitem__)
    if resultado_llm.categoria == resultado_reglas.categoria:
        categoria = resultado_llm.categoria
    elif ORDEN_PRIORIDAD[resultado_llm.prioridad] > ORDEN_PRIORIDAD[resultado_reglas.prioridad]:
        categoria = resultado_llm.categoria
    elif ORDEN_PRIORIDAD[resultado_reglas.prioridad] > ORDEN_PRIORIDAD[resultado_llm.prioridad]:
        categoria = resultado_reglas.categoria
    else:
        categoria = Categoria.seguridad
    return resultado_llm.model_copy(update={"prioridad": prioridad, "categoria": categoria}), coincide


def clasificar_correo(correo: str, modelo: str = MODELO_DEFAULT, reintentos: int = 2) -> tuple[Clasificacion, dict[str, Any]]:
    if not correo.strip():
        raise ValueError("El correo no puede estar vacío.")
    if reintentos < 1:
        raise ValueError("Debe permitirse al menos un intento de clasificación.")

    resultado_reglas = clasificar_por_reglas(correo)
    inicio = time.perf_counter()
    errores: list[str] = []
    resultado_llm: Clasificacion | None = None
    for _ in range(reintentos):
        try:
            respuesta = ollama.chat(
                model=modelo,
                format=Clasificacion.model_json_schema(),
                messages=[
                    {"role": "system", "content": "Clasifica el correo de logística en JSON con el esquema solicitado."},
                    {"role": "user", "content": _anonimizar(correo)},
                ],
            )
            contenido = respuesta["message"]["content"]
            resultado_llm = Clasificacion.model_validate_json(contenido)
            break
        except (ollama.ResponseError, httpx.HTTPError, ValidationError, ValueError, KeyError, TypeError) as error:
            errores.append(str(error))

    latencia_ms = round((time.perf_counter() - inicio) * 1000, 2)
    if resultado_llm is None:
        return resultado_reglas, {
            "fuente": "reglas_respaldo",
            "modelo": modelo,
            "latencia_ms": latencia_ms,
            "coincidio_con_reglas": None,
            "requiere_revision_humana": True,
            "errores": errores,
        }

    fusion, coinciden = fusionar_clasificaciones(resultado_llm, resultado_reglas)
    return fusion, {
        "fuente": "llm_hibrido",
        "modelo": modelo,
        "latencia_ms": latencia_ms,
        "coincidio_con_reglas": coinciden,
        "requiere_revision_humana": not coinciden,
        "errores": errores,
        "resultado_reglas": resultado_reglas.como_documento(),
        "resultado_llm": resultado_llm.como_documento(),
    }


def responder_con_reglas(pregunta: str) -> str:
    texto = (pregunta or "").strip()
    if not texto:
        return "Necesito que me hagas una pregunta para poder ayudarte."

    pregunta = unicodedata.normalize("NFKD", texto.casefold())
    pregunta = "".join(caracter for caracter in pregunta if not unicodedata.combining(caracter))

    if any(token in pregunta for token in ("acceso", "autoriz", "permiso", "entrada", "porton")):
        return (
            "Para autorizar un acceso, revisa la regla base: A = P ∧ S ∧ ¬Q. "
            "Además, si la certificación está vencida o hay material peligroso fuera del horario permitido, "
            "se bloquea el acceso o exige inspección."
        )
    if any(token in pregunta for token in ("incidente", "correo", "clasif", "alerta", "seguridad")):
        return (
            "El sistema clasifica incidentes por categoría y prioridad. Si el correo habla de derrame, robo, amenaza o accidente, "
            "tiene prioridad crítica; si es solo documentación o retraso, suele caer en documentación u operativo."
        )
    if any(token in pregunta for token in ("camion", "placa", "vehiculo", "conductor", "empresa")):
        return (
            "Puedes consultar camiones por placa, ID o empresa desde la pestaña de Camiones. "
            "También se valida la certificación del conductor y si el vehículo transporta material peligroso."
        )
    if any(token in pregunta for token in ("riesgo", "etico", "mitigacion", "probabilidad", "impacto")):
        return (
            "Los riesgos éticos se evalúan por probabilidad e impacto. El sistema calcula un puntaje y muestra la mitigación residual para priorizar acciones."
        )
    if any(token in pregunta for token in ("configur", "modelo", "llm", "simulaci")):
        return (
            "La configuración del sistema define el modelo LLM, el umbral de riesgo y si se trabaja en modo simulación. "
            "Puedes ajustar esto desde la pestaña de Configuración."
        )

    return (
        "Puedo ayudarte con acceso, incidentes, camiones, riesgos éticos y configuración del sistema. "
        "Cuéntame qué quieres revisar o resolver y te orientaré paso a paso."
    )


def responder_pregunta(pregunta: str, modelo: str = MODELO_DEFAULT, reintentos: int = 1) -> tuple[str, dict[str, Any]]:
    texto = (pregunta or "").strip()
    if not texto:
        raise ValueError("La pregunta no puede estar vacía.")
    if reintentos < 1:
        raise ValueError("Debe permitirse al menos un intento de respuesta.")

    inicio = time.perf_counter()
    errores: list[str] = []
    for _ in range(reintentos):
        try:
            respuesta = ollama.chat(
                model=modelo,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un agente de apoyo para logística y seguridad. Responde en español, de manera clara y útil. "
                            "Si no sabes algo, dilo honestamente y ofrece una guía práctica."
                        ),
                    },
                    {"role": "user", "content": texto},
                ],
            )
            contenido = str(respuesta["message"]["content"]).strip()
            if contenido:
                return contenido, {
                    "fuente": "llm",
                    "modelo": modelo,
                    "latencia_ms": round((time.perf_counter() - inicio) * 1000, 2),
                    "errores": errores,
                }
        except (ollama.ResponseError, httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            errores.append(str(error))

    respaldo = responder_con_reglas(texto)
    return respaldo, {
        "fuente": "reglas_respaldo",
        "modelo": modelo,
        "latencia_ms": round((time.perf_counter() - inicio) * 1000, 2),
        "errores": errores,
    }


@dataclass
class Configuracion:
    modelo: str = MODELO_DEFAULT
    umbral_riesgo: int = 15
    simulacion: bool = False

    @classmethod
    def cargar(cls, archivo: Path | None = None) -> "Configuracion":
        ruta = archivo or (Path(__file__).resolve().parent / "data" / "configuracion.json")
        if not ruta.exists():
            return cls()
        contenido: dict[str, Any] = json.loads(ruta.read_text(encoding="utf-8"))
        configuracion = cls(
            modelo=str(contenido.get("modelo", cls.modelo)).strip(),
            umbral_riesgo=int(contenido.get("umbral_riesgo", cls.umbral_riesgo)),
            simulacion=normalizar_bool(contenido.get("simulacion", cls.simulacion)),
        )
        if not configuracion.modelo:
            raise ValueError("El modelo configurado no puede estar vacío.")
        if not 1 <= configuracion.umbral_riesgo <= 25:
            raise ValueError("El umbral configurado debe estar entre 1 y 25.")
        return configuracion

    def guardar(self, archivo: Path | None = None) -> None:
        ruta = archivo or (Path(__file__).resolve().parent / "data" / "configuracion.json")
        if not self.modelo.strip():
            raise ValueError("El modelo no puede estar vacío.")
        if not 1 <= self.umbral_riesgo <= 25:
            raise ValueError("El umbral debe estar entre 1 y 25.")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")


class Servicio:
    def __init__(self, repositorio: Repositorio, modelo: str = MODELO_DEFAULT) -> None:
        self.repositorio = repositorio
        self.modelo = modelo

    def buscar_camion(self, placa_o_id: str) -> dict[str, Any] | None:
        texto = (placa_o_id or "").strip().casefold()
        if not texto:
            return None
        for camion in self.repositorio.listar("camiones"):
            if texto in {
                str(camion.get("placa", "")).casefold(),
                str(camion.get("camion_id", "")).casefold(),
                str(camion.get("_id", "")).casefold(),
            }:
                return camion
        return None

    def registrar_acceso(self, datos: dict[str, Any], operador: str) -> dict[str, Any]:
        camion = self.buscar_camion(str(datos.get("placa", "")))
        datos = dict(datos)
        if camion:
            datos["P"] = normalizar_bool(datos.get("P", False)) and bool(camion.get("autorizacion", False))
            vigencia = camion.get("certificacion_conductor")
            if vigencia:
                try:
                    datos["certificacion_vigente"] = datetime.fromisoformat(str(vigencia)).date() >= datetime.now().date()
                except ValueError as exc:
                    raise ValueError(f"Fecha de certificación inválida para {camion.get('placa', '')}.") from exc
            datos["materiales_peligrosos"] = normalizar_bool(datos.get("materiales_peligrosos", False)) or normalizar_bool(camion.get("materiales_peligrosos", False))
        acceso = crear_acceso(datos, operador)
        return self.repositorio.guardar("accesos", acceso)

    def clasificar_incidente(self, correo: str, simulacion: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
        if simulacion:
            clasificacion = clasificar_por_reglas(correo)
            metadatos = {"fuente": "simulacion_reglas", "modelo": self.modelo, "latencia_ms": 0.0, "coincidio_con_reglas": True, "requiere_revision_humana": True}
        else:
            clasificacion, metadatos = clasificar_correo(correo, modelo=self.modelo)
        incidente = incidente_nuevo(correo, clasificacion.como_documento())
        incidente["fuente"] = metadatos["fuente"]
        incidente["requiere_revision_humana"] = metadatos["requiere_revision_humana"]
        guardado = self.repositorio.guardar("incidentes", incidente)
        evaluacion = {
            "_id": guardado["_id"],
            "prompt": correo,
            "respuesta": clasificacion.como_documento(),
            "modelo": metadatos["modelo"],
            "latencia_ms": metadatos["latencia_ms"],
            "coincidio_con_reglas": metadatos.get("coincidio_con_reglas"),
            "fuente": metadatos["fuente"],
            "requiere_revision_humana": metadatos["requiere_revision_humana"],
            "errores": metadatos.get("errores", []),
            "fecha": datetime.now().astimezone().isoformat(),
        }
        self.repositorio.guardar("evaluaciones_llm", evaluacion)
        return guardado, metadatos

    def agregar_riesgo(self, datos: dict[str, Any]) -> dict[str, Any]:
        for campo in ("probabilidad", "impacto", "probabilidad_residual", "impacto_residual"):
            if campo in datos and not 1 <= int(datos[campo]) <= 5:
                raise ValueError(f"{campo} debe estar entre 1 y 5.")
        for campo in ("modulo", "descripcion", "categoria", "mitigacion"):
            if not str(datos.get(campo, "")).strip():
                raise ValueError(f"El campo {campo} es obligatorio.")
        nuevo = riesgo_nuevo(datos)
        anterior = self.repositorio.obtener("riesgos_eticos", nuevo["_id"])
        if anterior:
            nuevo["historial"] = list(anterior.get("historial", []))
            nuevo["historial"].append({
                "accion": "actualizado",
                "fecha": nuevo["fecha"],
                "modulo": nuevo["modulo"],
                "descripcion": nuevo["descripcion"],
                "categoria": nuevo["categoria"],
                "probabilidad": nuevo["probabilidad"],
                "impacto": nuevo["impacto"],
                "mitigacion": nuevo["mitigacion"],
                "probabilidad_residual": nuevo["probabilidad_residual"],
                "impacto_residual": nuevo["impacto_residual"],
                "puntaje": nuevo["puntaje"],
                "puntaje_residual": nuevo["puntaje_residual"],
            })
        return self.repositorio.guardar("riesgos_eticos", nuevo)


class Aplicacion:
    def __init__(self, raiz: tk.Tk) -> None:
        self.raiz = raiz
        self.raiz.title("Control de acceso, incidentes y riesgos éticos")
        self.raiz.geometry("1120x760")
        self.raiz.minsize(900, 620)
        self.repositorio = Repositorio()
        self.configuracion = Configuracion.cargar()
        self.servicio = Servicio(self.repositorio, self.configuracion.modelo)
        self._configurar_estilos()
        self._crear_interfaz()

    def _configurar_estilos(self) -> None:
        estilo = ttk.Style(self.raiz)
        estilo.theme_use("clam")
        self.raiz.configure(background="#eef2f7")
        estilo.configure(".", background="#eef2f7", foreground="#1f2937", font=("Segoe UI", 10))
        estilo.configure("TFrame", background="#eef2f7")
        estilo.configure("TLabel", background="#eef2f7", foreground="#1f2937")
        estilo.configure("Header.TFrame", background="#14243a")
        estilo.configure("HeaderTitle.TLabel", background="#14243a", foreground="#ffffff", font=("Segoe UI", 17, "bold"))
        estilo.configure("HeaderStatus.TLabel", background="#14243a", foreground="#bfdbfe", font=("Segoe UI", 9))
        estilo.configure("TNotebook", background="#eef2f7", borderwidth=0, tabmargins=(2, 7, 2, 0))
        estilo.configure("TNotebook.Tab", background="#dce5f0", foreground="#334155", padding=(13, 8), font=("Segoe UI", 9, "bold"))
        estilo.map("TNotebook.Tab", background=[("selected", "#2563eb"), ("active", "#bfdbfe")], foreground=[("selected", "#ffffff"), ("active", "#14243a")])
        estilo.configure("TButton", background="#ffffff", foreground="#1e3a5f", padding=(11, 7), borderwidth=0, font=("Segoe UI", 9, "bold"))
        estilo.map("TButton", background=[("active", "#dbeafe"), ("disabled", "#e5e7eb")], foreground=[("disabled", "#94a3b8")])
        estilo.configure("Accent.TButton", background="#2563eb", foreground="#ffffff", padding=(15, 8), font=("Segoe UI", 10, "bold"))
        estilo.map("Accent.TButton", background=[("active", "#1d4ed8"), ("disabled", "#94a3b8")], foreground=[("disabled", "#f8fafc")])
        estilo.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#1f2937", rowheight=28, borderwidth=0, font=("Segoe UI", 9))
        estilo.configure("Treeview.Heading", background="#1e3a5f", foreground="#ffffff", padding=(8, 7), font=("Segoe UI", 9, "bold"))
        estilo.map("Treeview", background=[("selected", "#bfdbfe")], foreground=[("selected", "#14243a")])
        estilo.configure("TEntry", fieldbackground="#ffffff", foreground="#1f2937", padding=6)

    @staticmethod
    def _tabla(padre: ttk.Frame, columnas: tuple[str, ...], alturas: int = 12) -> ttk.Treeview:
        tabla = ttk.Treeview(padre, columns=columnas, show="headings", height=alturas, selectmode="browse")
        for columna in columnas:
            tabla.heading(columna, text=columna.replace("_", " ").title())
            tabla.column(columna, width=145, anchor="w")
        barra = ttk.Scrollbar(padre, orient="vertical", command=tabla.yview)
        barra_horizontal = ttk.Scrollbar(padre, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=barra.set, xscrollcommand=barra_horizontal.set)
        barra.pack(side="right", fill="y")
        barra_horizontal.pack(side="bottom", fill="x")
        tabla.pack(side="left", fill="both", expand=True)
        return tabla

    @staticmethod
    def _seleccion(tabla: ttk.Treeview) -> str | None:
        seleccion = tabla.selection()
        return seleccion[0] if seleccion else None

    def _crear_interfaz(self) -> None:
        encabezado = ttk.Frame(self.raiz, padding=(18, 13), style="Header.TFrame")
        encabezado.pack(fill="x")
        ttk.Label(encabezado, text="Centro de operaciones de acceso", style="HeaderTitle.TLabel").pack(side="left")
        self.estado_conexion = tk.StringVar(value=self.repositorio.modo)
        ttk.Label(encabezado, textvariable=self.estado_conexion, style="HeaderStatus.TLabel").pack(side="right")

        self.pestanas = ttk.Notebook(self.raiz)
        self.pestanas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.tab_panel = ttk.Frame(self.pestanas, padding=12)
        self.tab_acceso = ttk.Frame(self.pestanas, padding=12)
        self.tab_verdad = ttk.Frame(self.pestanas, padding=12)
        self.tab_incidentes = ttk.Frame(self.pestanas, padding=12)
        self.tab_camiones = ttk.Frame(self.pestanas, padding=12)
        self.tab_riesgos = ttk.Frame(self.pestanas, padding=12)
        self.tab_chat = ttk.Frame(self.pestanas, padding=12)
        self.tab_config = ttk.Frame(self.pestanas, padding=12)
        for pestaña, titulo in (
            (self.tab_panel, "Panel"),
            (self.tab_acceso, "Control de acceso"),
            (self.tab_verdad, "Reglas / tabla de verdad"),
            (self.tab_incidentes, "Incidentes"),
            (self.tab_camiones, "Camiones"),
            (self.tab_riesgos, "Riesgos éticos"),
            (self.tab_chat, "Asistente IA"),
            (self.tab_config, "Configuración"),
        ):
            self.pestanas.add(pestaña, text=titulo)

        self._crear_panel()
        self._crear_acceso()
        self._crear_tabla_verdad()
        self._crear_incidentes()
        self._crear_camiones()
        self._crear_riesgos()
        self._crear_chat()
        self._crear_configuracion()

    def _crear_chat(self) -> None:
        self.tab_chat.columnconfigure(0, weight=1)
        self.tab_chat.rowconfigure(1, weight=1)
        ttk.Label(self.tab_chat, text="Asistente de IA para logística", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(self.tab_chat, text="Haz cualquier pregunta sobre accesos, incidentes, camiones o riesgos.", wraplength=820).grid(row=1, column=0, sticky="w", pady=(4, 8))

        self.pregunta_agente = tk.Text(self.tab_chat, height=5, wrap="word")
        self.pregunta_agente.grid(row=2, column=0, sticky="nsew", pady=(0, 8))

        fila_chat = ttk.Frame(self.tab_chat)
        fila_chat.grid(row=3, column=0, sticky="w")
        ttk.Button(fila_chat, text="Preguntar", command=self._preguntar_agente).pack(side="left")
        self.estado_agente = tk.StringVar(value="Listo.")
        ttk.Label(fila_chat, textvariable=self.estado_agente).pack(side="left", padx=(12, 0))

        ttk.Label(self.tab_chat, text="Respuesta del agente").grid(row=4, column=0, sticky="w", pady=(12, 4))
        self.respuesta_agente = tk.Text(self.tab_chat, height=11, wrap="word", state="disabled")
        self.respuesta_agente.grid(row=5, column=0, sticky="nsew")

    def _preguntar_agente(self) -> None:
        pregunta = self.pregunta_agente.get("1.0", "end").strip()
        if not pregunta:
            messagebox.showwarning("Pregunta vacía", "Escribe una pregunta antes de consultar al agente.", parent=self.raiz)
            return
        try:
            respuesta, metadatos = responder_pregunta(pregunta, modelo=self.configuracion.modelo)
            self.respuesta_agente.configure(state="normal")
            self.respuesta_agente.delete("1.0", "end")
            self.respuesta_agente.insert("1.0", respuesta)
            self.respuesta_agente.configure(state="disabled")
            self.estado_agente.set(f"Fuente: {metadatos['fuente']} | {metadatos['latencia_ms']} ms")
            guardado = {
                "_id": identificador(),
                "prompt": pregunta,
                "respuesta": respuesta,
                "modelo": metadatos.get("modelo", self.configuracion.modelo),
                "fuente": metadatos.get("fuente", "reglas_respaldo"),
                "latencia_ms": metadatos.get("latencia_ms", 0),
                "fecha": datetime.now(timezone.utc).isoformat(),
            }
            self.repositorio.guardar("evaluaciones_llm", guardado)
        except Exception as error:
            self.estado_agente.set("No se pudo responder la pregunta.")
            messagebox.showerror("Agente IA", str(error), parent=self.raiz)

    def _crear_panel(self) -> None:
        self.tab_panel.columnconfigure(0, weight=1)
        ttk.Label(self.tab_panel, text="Indicadores del sistema", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        filtros = ttk.Frame(self.tab_panel)
        filtros.grid(row=1, column=0, sticky="ew", pady=8)
        ttk.Label(filtros, text="Desde:").pack(side="left")
        self.fecha_desde = ttk.Entry(filtros, width=13)
        self.fecha_desde.pack(side="left", padx=(4, 12))
        ttk.Label(filtros, text="Hasta:").pack(side="left")
        self.fecha_hasta = ttk.Entry(filtros, width=13)
        self.fecha_hasta.pack(side="left", padx=4)
        ttk.Button(filtros, text="Actualizar", command=self._actualizar_panel).pack(side="left", padx=10)
        self.indicadores = tk.StringVar()
        ttk.Label(self.tab_panel, textvariable=self.indicadores, font=("Segoe UI", 11)).grid(row=2, column=0, sticky="w", pady=6)
        ttk.Label(self.tab_panel, text="Incidentes por categoría y semana ISO", font=("Segoe UI", 12, "bold")).grid(row=3, column=0, sticky="w", pady=(15, 5))
        self.tabla_agregacion = self._tabla(ttk.Frame(self.tab_panel), ("categoria", "anio", "semana", "total"), 8)
        self.tabla_agregacion.master.grid(row=4, column=0, sticky="nsew")
        self.tab_panel.rowconfigure(4, weight=1)
        self._actualizar_panel()

    def _actualizar_panel(self) -> None:
        inicio = self.fecha_desde.get().strip() if hasattr(self, "fecha_desde") else ""
        fin = self.fecha_hasta.get().strip() if hasattr(self, "fecha_hasta") else ""
        try:
            if inicio:
                datetime.strptime(inicio, "%Y-%m-%d")
            if fin:
                datetime.strptime(fin, "%Y-%m-%d")
            if inicio and fin and inicio > fin:
                raise ValueError("La fecha inicial no puede ser posterior a la final.")
        except ValueError as error:
            messagebox.showerror("Fechas inválidas", str(error), parent=self.raiz)
            return

        accesos = self.repositorio.listar("accesos")
        incidentes = self.repositorio.listar("incidentes")
        riesgos = self.repositorio.listar("riesgos_eticos")

        def dentro(documento: dict[str, Any]) -> bool:
            fecha = str(documento.get("fecha", ""))[:10]
            return (not inicio or fecha >= inicio) and (not fin or fecha <= fin)

        self.indicadores.set(
            f"Camiones atendidos: {sum(dentro(x) for x in accesos)}    |    "
            f"Incidentes abiertos: {sum(x.get('estado') != 'cerrado' and dentro(x) for x in incidentes)}"
            f"    |    Riesgos críticos: {sum(x.get('puntaje', 0) >= 15 for x in riesgos)}"
        )
        self.tabla_agregacion.delete(*self.tabla_agregacion.get_children())
        for fila in self.repositorio.incidentes_por_categoria_semana():
            self.tabla_agregacion.insert("", "end", values=(fila["categoria"], fila["anio"], fila["semana"], fila["total"]))

    def _crear_acceso(self) -> None:
        marco = self.tab_acceso
        marco.columnconfigure(0, weight=1)
        ttk.Label(marco, text="Reglas originales: A = P ∧ S ∧ ¬Q; E = P ∧ (R ∨ Q).", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(marco, text="Reglas adicionales: certificación vigente para autorizar; material peligroso fuera de horario requiere inspección.", wraplength=800).grid(row=1, column=0, sticky="w", pady=(4, 12))

        fila = ttk.Frame(marco)
        fila.grid(row=2, column=0, sticky="ew")
        fila.columnconfigure(1, weight=1)
        ttk.Label(fila, text="Placa:").grid(row=0, column=0, sticky="w")
        self.placa_acceso = ttk.Entry(fila, width=18)
        self.placa_acceso.grid(row=0, column=1, sticky="ew", padx=(4, 16))
        ttk.Button(fila, text="Buscar camión", command=self._buscar_camion).grid(row=0, column=2, sticky="w")

        self.bits = {nombre: tk.BooleanVar(value=False) for nombre in ("P", "Q", "R", "S")}
        self.certificacion_vigente = tk.BooleanVar(value=True)
        self.materiales_peligrosos = tk.BooleanVar(value=False)
        self.horario_permitido = tk.BooleanVar(value=True)
        controles = ttk.Frame(marco)
        controles.grid(row=3, column=0, sticky="w", pady=12)
        for nombre, significado in (("P", "Preautorizado"), ("Q", "Alerta"), ("R", "Carga de riesgo"), ("S", "Documentación completa")):
            ttk.Checkbutton(controles, text=f"{nombre}: {significado}", variable=self.bits[nombre], command=self._actualizar_logica).pack(side="left", padx=6)
        ttk.Checkbutton(controles, text="Certificación vigente", variable=self.certificacion_vigente, command=self._actualizar_logica).pack(side="left", padx=6)
        ttk.Checkbutton(controles, text="Materiales peligrosos", variable=self.materiales_peligrosos, command=self._actualizar_logica).pack(side="left", padx=6)
        ttk.Checkbutton(controles, text="Horario permitido", variable=self.horario_permitido, command=self._actualizar_logica).pack(side="left", padx=6)

        self.salidas_logicas = tk.StringVar(value="A=... | E=... | ACCESO")
        ttk.Label(marco, textvariable=self.salidas_logicas, font=("Segoe UI", 12, "bold")).grid(row=4, column=0, sticky="w", pady=(6, 12))

        self.operador_acceso = ttk.Entry(marco, width=20)
        self.operador_acceso.insert(0, "operador")
        ttk.Label(marco, text="Operador:").grid(row=5, column=0, sticky="w")
        self.operador_acceso.grid(row=6, column=0, sticky="w", pady=(2, 10))
        ttk.Button(marco, text="Registrar acceso", command=self._registrar_acceso).grid(row=7, column=0, sticky="w")

        ttk.Label(marco, text="Bitácora de accesos").grid(row=8, column=0, sticky="w", pady=(12, 4))
        self.tabla_accesos = self._tabla(ttk.Frame(marco), ("_id", "fecha", "placa", "acceso_autorizado", "requiere_inspeccion", "operador"), 7)
        self.tabla_accesos.master.grid(row=9, column=0, sticky="nsew")
        marco.rowconfigure(9, weight=1)

        self._actualizar_logica()
        self._actualizar_accesos()

    def _datos_regla(self) -> dict[str, Any]:
        return {
            **{nombre: variable.get() for nombre, variable in self.bits.items()},
            "certificacion_vigente": self.certificacion_vigente.get(),
            "materiales_peligrosos": self.materiales_peligrosos.get(),
            "horario_permitido": self.horario_permitido.get(),
        }

    def _actualizar_logica(self) -> None:
        resultado = evaluar_acceso(**self._datos_regla())
        decision = (
            "REVISIÓN / INSPECCIÓN"
            if resultado["requiere_inspeccion"] or resultado["certificacion_bloquea"]
            else "ACCESO AUTORIZADO"
            if resultado["acceso_autorizado"]
            else "ACCESO NO AUTORIZADO"
        )
        self.salidas_logicas.set(f"A={resultado['A']} | E={resultado['E']} | {decision}")

    def _buscar_camion(self) -> None:
        camion = self.servicio.buscar_camion(self.placa_acceso.get())
        if not camion:
            messagebox.showinfo("Búsqueda", "No se encontró el camión.", parent=self.raiz)
            return
        self.bits["P"].set(bool(camion.get("autorizacion", False)))
        vigencia = camion.get("certificacion_conductor", "")
        try:
            vigente = datetime.fromisoformat(str(vigencia)).date() >= datetime.now().date()
        except (TypeError, ValueError):
            vigente = False
        self.certificacion_vigente.set(vigente)
        self.materiales_peligrosos.set(bool(camion.get("materiales_peligrosos", False)))
        self._actualizar_logica()

    def _registrar_acceso(self) -> None:
        try:
            datos = self._datos_regla()
            datos["placa"] = self.placa_acceso.get()
            documento = self.servicio.registrar_acceso(datos, self.operador_acceso.get())
        except (ValueError, KeyError, ConnectionError) as error:
            messagebox.showerror("No se guardó el acceso", str(error), parent=self.raiz)
            return
        messagebox.showinfo("Resultado", "\n".join(documento["explicacion"]), parent=self.raiz)
        self._actualizar_accesos()
        self._actualizar_panel()

    def _actualizar_accesos(self) -> None:
        if not hasattr(self, "tabla_accesos"):
            return
        self.tabla_accesos.delete(*self.tabla_accesos.get_children())
        for acceso in reversed(self.repositorio.listar("accesos")):
            self.tabla_accesos.insert(
                "",
                "end",
                iid=str(acceso["_id"]),
                values=(
                    acceso["_id"],
                    str(acceso.get("fecha", ""))[:19],
                    acceso.get("placa", ""),
                    acceso.get("acceso_autorizado", False),
                    acceso.get("requiere_inspeccion", False),
                    acceso.get("operador", ""),
                ),
            )

    def _crear_tabla_verdad(self) -> None:
        ttk.Label(self.tab_verdad, text="Activa o desactiva premisas para recalcular A y E.", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        controles = ttk.Frame(self.tab_verdad)
        controles.pack(anchor="w", pady=5)
        self.bits_verdad = {nombre: tk.BooleanVar(value=valor) for nombre, valor in (("P", False), ("Q", False), ("R", False), ("S", False), ("V", True), ("H", False), ("T", True))}
        for nombre, significado in (("P", "Preautorizado"), ("Q", "Alerta"), ("R", "Carga de riesgo"), ("S", "Documentación completa"), ("V", "Certificación vigente"), ("H", "Material peligroso"), ("T", "Horario permitido")):
            ttk.Checkbutton(controles, text=f"{nombre}: {significado}", variable=self.bits_verdad[nombre], command=self._simular_verdad).pack(side="left", padx=8)
        self.resultado_verdad = tk.StringVar()
        ttk.Label(self.tab_verdad, textvariable=self.resultado_verdad, font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=10)
        tabla_frame = ttk.Frame(self.tab_verdad)
        tabla_frame.pack(fill="both", expand=True)
        self.tabla_completa_verdad = self._tabla(tabla_frame, ("P", "Q", "R", "S", "V", "H", "T", "A", "E", "bloqueo_certificacion", "bloqueo_horario", "A_final", "E_final"), 16)
        for fila in generar_tabla_verdad_extendida():
            self.tabla_completa_verdad.insert("", "end", values=tuple(int(fila[columna]) for columna in ("P", "Q", "R", "S", "V", "H", "T", "A", "E", "bloqueo_certificacion", "bloqueo_horario", "A_final", "E_final")))
        self._simular_verdad()

    def _simular_verdad(self) -> None:
        datos = {nombre: variable.get() for nombre, variable in self.bits_verdad.items()}
        resultado = evaluar_acceso(datos["P"], datos["Q"], datos["R"], datos["S"], certificacion_vigente=datos["V"], materiales_peligrosos=datos["H"], horario_permitido=datos["T"])
        self.resultado_verdad.set(f"A={int(resultado['A'])}   |   E={int(resultado['E'])}   |   A = P ∧ S ∧ ¬Q; E = P ∧ (R ∨ Q)")

    def _crear_incidentes(self) -> None:
        self.tab_incidentes.columnconfigure(0, weight=1)
        self.tab_incidentes.rowconfigure(1, weight=1)
        ttk.Label(self.tab_incidentes, text="Pega un correo; el LLM local clasifica y las reglas actúan como respaldo.").grid(row=0, column=0, sticky="w")
        self.correo_incidente = tk.Text(self.tab_incidentes, height=5, wrap="word")
        self.correo_incidente.grid(row=1, column=0, sticky="nsew", pady=6)
        fila_botones = ttk.Frame(self.tab_incidentes)
        fila_botones.grid(row=2, column=0, sticky="ew")
        self.estado_incidente = tk.StringVar(value="Listo.")
        ttk.Label(fila_botones, textvariable=self.estado_incidente).pack(side="left")
        ttk.Button(fila_botones, text="Clasificar correo", command=self._clasificar_incidente).pack(side="left", padx=(12, 0))
        ttk.Label(self.tab_incidentes, text="Historial de incidentes").grid(row=3, column=0, sticky="w", pady=(12, 4))
        self.tabla_incidentes = self._tabla(ttk.Frame(self.tab_incidentes), ("_id", "categoria", "prioridad", "estado", "fecha"), 9)
        self.tabla_incidentes.master.grid(row=4, column=0, sticky="nsew")
        self.tab_incidentes.rowconfigure(4, weight=1)
        self._actualizar_incidentes()

    def _clasificar_incidente(self) -> None:
        correo = self.correo_incidente.get("1.0", "end").strip()
        if not correo:
            messagebox.showwarning("Correo vacío", "Escribe un correo antes de clasificar.", parent=self.raiz)
            return
        try:
            guardado, _ = self.servicio.clasificar_incidente(correo, simulacion=False)
            self.estado_incidente.set(f"Clasificación guardada: {guardado.get('categoria', 'desconocida')} / {guardado.get('prioridad', 'sin prioridad')}.")
        except Exception as error:
            self.estado_incidente.set("No se pudo clasificar el correo.")
            messagebox.showerror("Clasificación", str(error), parent=self.raiz)
            return
        self._actualizar_incidentes()
        self._actualizar_panel()

    def _actualizar_incidentes(self) -> None:
        if not hasattr(self, "tabla_incidentes"):
            return
        self.tabla_incidentes.delete(*self.tabla_incidentes.get_children())
        for incidente in reversed(self.repositorio.listar("incidentes")):
            self.tabla_incidentes.insert("", "end", iid=str(incidente["_id"]), values=(incidente["_id"], incidente.get("categoria", ""), incidente.get("prioridad", ""), incidente.get("estado", ""), str(incidente.get("fecha", ""))[:19]))

    def _crear_camiones(self) -> None:
        ttk.Label(self.tab_camiones, text="Registro de camiones").pack(anchor="w")
        self.tabla_camiones = self._tabla(ttk.Frame(self.tab_camiones), ("_id", "placa", "camion_id", "empresa", "autorizacion", "certificacion_conductor"), 17)
        self.tabla_camiones.master.pack(fill="both", expand=True, pady=6)
        botones = ttk.Frame(self.tab_camiones)
        botones.pack(anchor="e")
        ttk.Button(botones, text="Nuevo", command=self._dialogo_camion).pack(side="left", padx=3)
        ttk.Button(botones, text="Editar", command=self._editar_camion).pack(side="left", padx=3)
        ttk.Button(botones, text="Eliminar", command=self._eliminar_camion).pack(side="left", padx=3)
        self._actualizar_camiones()

    def _dialogo_camion(self, camion: dict[str, Any] | None = None) -> None:
        camion = camion or {}
        dialogo = tk.Toplevel(self.raiz)
        dialogo.title("Camión")
        dialogo.transient(self.raiz)
        dialogo.grab_set()
        campos = (("placa", "Placa"), ("camion_id", "ID de camión"), ("empresa", "Empresa"), ("certificacion_conductor", "Certificación (AAAA-MM-DD)"))
        entradas: dict[str, ttk.Entry] = {}
        for index, (campo, etiqueta) in enumerate(campos):
            ttk.Label(dialogo, text=etiqueta).grid(row=index, column=0, padx=8, pady=5, sticky="w")
            entrada = ttk.Entry(dialogo, width=34)
            entrada.insert(0, str(camion.get(campo, "")))
            entrada.grid(row=index, column=1, padx=8, pady=5)
            entradas[campo] = entrada
        autorizado = tk.BooleanVar(value=bool(camion.get("autorizacion", False)))
        peligroso = tk.BooleanVar(value=bool(camion.get("materiales_peligrosos", False)))
        ttk.Checkbutton(dialogo, text="Autorizado", variable=autorizado).grid(row=4, column=0, padx=8, pady=5)
        ttk.Checkbutton(dialogo, text="Material peligroso", variable=peligroso).grid(row=4, column=1, padx=8, pady=5)

        def guardar() -> None:
            documento = {campo: entrada.get().strip() for campo, entrada in entradas.items()}
            if not all(documento.values()):
                messagebox.showerror("Validación", "Todos los campos de texto son obligatorios.", parent=dialogo)
                return
            try:
                datetime.strptime(documento["certificacion_conductor"], "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Fecha inválida", "Usa el formato AAAA-MM-DD.", parent=dialogo)
                return
            documento["_id"] = camion.get("_id") or documento["camion_id"]
            documento["autorizacion"] = autorizado.get()
            documento["materiales_peligrosos"] = peligroso.get()
            self.repositorio.guardar("camiones", documento)
            dialogo.destroy()
            self._actualizar_camiones()
            self._actualizar_panel()

        ttk.Button(dialogo, text="Guardar", command=guardar).grid(row=5, column=0, columnspan=2, pady=10)

    def _actualizar_camiones(self) -> None:
        if not hasattr(self, "tabla_camiones"):
            return
        self.tabla_camiones.delete(*self.tabla_camiones.get_children())
        for camion in self.repositorio.listar("camiones"):
            self.tabla_camiones.insert("", "end", iid=str(camion["_id"]), values=(camion.get("_id", ""), camion.get("placa", ""), camion.get("camion_id", ""), camion.get("empresa", ""), camion.get("autorizacion", False), camion.get("certificacion_conductor", "")))

    def _editar_camion(self) -> None:
        camion_id = self._seleccion(self.tabla_camiones)
        camion = self.repositorio.obtener("camiones", camion_id) if camion_id else None
        if camion:
            self._dialogo_camion(camion)

    def _eliminar_camion(self) -> None:
        camion_id = self._seleccion(self.tabla_camiones)
        if camion_id and messagebox.askyesno("Confirmar", "¿Eliminar este camión?", parent=self.raiz):
            self.repositorio.eliminar("camiones", camion_id)
            self._actualizar_camiones()
            self._actualizar_panel()

    def _crear_riesgos(self) -> None:
        marco = ttk.Frame(self.tab_riesgos)
        marco.pack(fill="both", expand=True)
        marco.columnconfigure(0, weight=3)
        marco.columnconfigure(1, weight=2)
        tabla_frame = ttk.Frame(marco)
        tabla_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.tabla_riesgos = self._tabla(tabla_frame, ("_id", "modulo", "categoria", "puntaje", "puntaje_residual", "mitigacion"), 16)
        botones = ttk.Frame(marco)
        botones.grid(row=1, column=0, sticky="e", pady=6)
        ttk.Button(botones, text="Nuevo", command=self._dialogo_riesgo).pack(side="left", padx=3)
        ttk.Button(botones, text="Editar", command=self._editar_riesgo).pack(side="left", padx=3)
        ttk.Button(botones, text="Eliminar", command=self._eliminar_riesgo).pack(side="left", padx=3)
        self.grafica_riesgos = tk.Canvas(marco, width=380, height=440, background="white", highlightthickness=1, highlightbackground="#cccccc")
        self.grafica_riesgos.grid(row=0, column=1, rowspan=2, sticky="nsew")
        self._actualizar_riesgos()

    def _dialogo_riesgo(self, riesgo: dict[str, Any] | None = None) -> None:
        riesgo = riesgo or {}
        dialogo = tk.Toplevel(self.raiz)
        dialogo.title("Riesgo ético")
        dialogo.transient(self.raiz)
        dialogo.grab_set()
        campos = (("modulo", "Módulo"), ("descripcion", "Descripción"), ("categoria", "Categoría"), ("probabilidad", "Probabilidad (1-5)"), ("impacto", "Impacto (1-5)"), ("mitigacion", "Mitigación"), ("probabilidad_residual", "Probabilidad residual (1-5)"), ("impacto_residual", "Impacto residual (1-5)"))
        entradas: dict[str, ttk.Entry] = {}
        for index, (campo, etiqueta) in enumerate(campos):
            ttk.Label(dialogo, text=etiqueta).grid(row=index, column=0, padx=8, pady=4, sticky="w")
            entrada = ttk.Entry(dialogo, width=45)
            entrada.insert(0, str(riesgo.get(campo, 3 if "probabilidad" in campo or "impacto" in campo else "")))
            entrada.grid(row=index, column=1, padx=8, pady=4)
            entradas[campo] = entrada

        def guardar() -> None:
            datos = {campo: entrada.get().strip() for campo, entrada in entradas.items()}
            try:
                for campo in ("probabilidad", "impacto", "probabilidad_residual", "impacto_residual"):
                    datos[campo] = int(datos[campo])
                    if not 1 <= datos[campo] <= 5:
                        raise ValueError
            except ValueError:
                messagebox.showerror("Validación", "Probabilidad e impacto deben estar entre 1 y 5.", parent=dialogo)
                return
            if not all(str(datos.get(campo, "")).strip() for campo in ("modulo", "descripcion", "categoria", "mitigacion")):
                messagebox.showerror("Validación", "Completa módulo, descripción, categoría y mitigación.", parent=dialogo)
                return
            datos["_id"] = riesgo.get("_id") or identificador()
            self.servicio.agregar_riesgo(datos)
            dialogo.destroy()
            self._actualizar_riesgos()
            self._actualizar_panel()

        ttk.Button(dialogo, text="Guardar", command=guardar).grid(row=8, column=0, columnspan=2, pady=10)

    def _actualizar_riesgos(self) -> None:
        if not hasattr(self, "tabla_riesgos"):
            return
        riesgos = self.repositorio.listar("riesgos_eticos")
        self.tabla_riesgos.delete(*self.tabla_riesgos.get_children())
        for riesgo in riesgos:
            self.tabla_riesgos.insert("", "end", iid=str(riesgo["_id"]), values=(riesgo.get("_id", ""), riesgo.get("modulo", ""), riesgo.get("categoria", ""), riesgo.get("puntaje", ""), riesgo.get("puntaje_residual", ""), riesgo.get("mitigacion", "")))

        self.grafica_riesgos.delete("all")
        if not riesgos:
            return
        maximo = max(int(riesgo.get("puntaje", 0)) for riesgo in riesgos)
        ancho_barra = 30
        espacio = 12
        inicio_x = 30
        ancho_canvas = 380
        for indice, riesgo in enumerate(riesgos):
            altura = int(riesgo.get("puntaje", 0)) / maximo * 250 if maximo else 0
            residual = min(int(riesgo.get("puntaje_residual", 0)), maximo) / maximo * 250 if maximo else 0
            x0 = inicio_x + indice * (ancho_barra + espacio)
            y0 = 300
            self.grafica_riesgos.create_rectangle(x0, y0 - altura, x0 + ancho_barra, y0, fill="#ef4444", outline="#b91c1c")
            self.grafica_riesgos.create_rectangle(x0 + 8, y0 - residual, x0 + ancho_barra + 8, y0, fill="#60a5fa", outline="#2563eb")
            self.grafica_riesgos.create_text(x0 + ancho_barra / 2, 320, text=str(riesgo.get("modulo", "")[:9]), font=("Segoe UI", 8))
        self.grafica_riesgos.create_line(20, 300, ancho_canvas - 20, 300, fill="#475569")

    def _editar_riesgo(self) -> None:
        riesgo_id = self._seleccion(self.tabla_riesgos)
        riesgo = self.repositorio.obtener("riesgos_eticos", riesgo_id) if riesgo_id else None
        if riesgo:
            self._dialogo_riesgo(riesgo)

    def _eliminar_riesgo(self) -> None:
        riesgo_id = self._seleccion(self.tabla_riesgos)
        if riesgo_id and messagebox.askyesno("Confirmar", "¿Eliminar este riesgo?", parent=self.raiz):
            self.repositorio.eliminar("riesgos_eticos", riesgo_id)
            self._actualizar_riesgos()
            self._actualizar_panel()

    def _crear_configuracion(self) -> None:
        ttk.Label(self.tab_config, text="Configuración del sistema", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        marco = ttk.Frame(self.tab_config, padding=10)
        marco.pack(fill="x")
        ttk.Label(marco, text="Modelo LLM:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.modelo_config = ttk.Entry(marco, width=30)
        self.modelo_config.insert(0, self.configuracion.modelo)
        self.modelo_config.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(marco, text="Umbral riesgo:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.umbral_config = ttk.Entry(marco, width=10)
        self.umbral_config.insert(0, str(self.configuracion.umbral_riesgo))
        self.umbral_config.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.simulacion_config = tk.BooleanVar(value=self.configuracion.simulacion)
        ttk.Checkbutton(marco, text="Modo simulación", variable=self.simulacion_config).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        ttk.Button(marco, text="Guardar configuración", command=self._guardar_configuracion).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=10)

    def _guardar_configuracion(self) -> None:
        try:
            self.configuracion = Configuracion(
                modelo=self.modelo_config.get().strip() or MODELO_DEFAULT,
                umbral_riesgo=int(self.umbral_config.get()),
                simulacion=self.simulacion_config.get(),
            )
            self.configuracion.guardar()
            self.servicio = Servicio(self.repositorio, self.configuracion.modelo)
            messagebox.showinfo("Configuración", "Se guardó la configuración correctamente.", parent=self.raiz)
        except ValueError as error:
            messagebox.showerror("Configuración inválida", str(error), parent=self.raiz)


def main() -> None:
    raiz = tk.Tk()
    Aplicacion(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
