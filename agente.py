import os
import threading
from datetime import datetime
import random
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox


class AgenteClimatizacion:
    def __init__(self):
        self.temperatura = 0.0
        self.humedad = 0.0
        self.accion = ""

    def percibir(self, temperatura: float, humedad: float):
        self.temperatura = float(temperatura)
        self.humedad = float(humedad)

    def tomar_decision(self) -> str:
        if self.temperatura > 30 and self.humedad > 70:
            self.accion = "Encender aire acondicionado (Modo Deshumidificador)"
        elif self.temperatura > 30:
            self.accion = "Encender ventilador"
        elif self.temperatura < 18:
            self.accion = "Encender calefacción"
        else:
            self.accion = "Mantener sistema apagado"
        return self.accion

    def obtener_estilo_accion(self) -> str:
        if "Deshumidificador" in self.accion:
            return "warning"
        elif "ventilador" in self.accion:
            return "info"
        elif "calefacción" in self.accion:
            return "danger"
        else:
            return "success"


class MongoClusterManager:
    def __init__(self):
        load_dotenv()
        self.user = os.getenv("MONGO_USER")
        self.password = os.getenv("MONGO_PASSWORD")
        self.cluster = os.getenv("MONGO_CLUSTER")
        self.db_name = os.getenv("MONGO_DB")
        self.collection_name = os.getenv("MONGO_COLLECTION")

        self.client = None
        self.db = None
        self.collection = None
        self.is_connected = False
        self.last_error = ""

    def get_uri(self) -> str:
        if not all([self.user, self.password, self.cluster]):
            raise ValueError("Faltan variables de entorno para la conexión de MongoDB (.env).")
        return f"mongodb+srv://{self.user}:{self.password}@{self.cluster}/?retryWrites=true&w=majority"

    def connect(self) -> bool:
        try:
            uri = self.get_uri()
            self.client = MongoClient(uri, serverSelectionTimeoutMS=6000)
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            self.is_connected = True
            self.last_error = ""
            return True
        except Exception as e:
            self.is_connected = False
            self.last_error = str(e)
            return False

    def insert_lectura(self, alumno: str, temperatura: float, humedad: float, accion: str) -> str:
        if not self.is_connected or self.collection is None:
            if not self.connect():
                raise ConnectionFailure(f"No hay conexión con el clúster: {self.last_error}")

        documento = {
            "alumno": alumno,
            "temperatura": round(float(temperatura), 2),
            "humedad": round(float(humedad), 2),
            "accion": accion,
            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": datetime.now()
        }

        resultado = self.collection.insert_one(documento)
        return str(resultado.inserted_id)

    def obtener_ultimos_registros(self, limit: int = 15) -> list:
        if not self.is_connected or self.collection is None:
            if not self.connect():
                return []
        try:
            cursor = self.collection.find().sort("_id", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            self.last_error = str(e)
            return []


class AgenteClimatizacionGUI:
    def __init__(self, root: tb.Window):
        self.root = root
        self.root.title("Agente de Climatización - MongoDB Atlas")
        self.root.geometry("1060x800")
        self.root.minsize(920, 700)

        self.agente = AgenteClimatizacion()
        self.mongo = MongoClusterManager()

        self.var_alumno = tb.StringVar(value=os.getenv("MONGO_DB", "Manuel"))
        self.var_temp = tb.DoubleVar(value=24.5)
        self.var_hum = tb.DoubleVar(value=55.0)
        self.var_status_cluster = tb.StringVar(value="Verificando conexión al Clúster...")
        self.var_decision = tb.StringVar(value="Esperando percepción inicial...")
        self.var_ultimo_id = tb.StringVar(value="Ninguno")
        self.var_ultima_hora = tb.StringVar(value="--:--:--")

        self._crear_interfaz()
        self._probar_conexion_async(notificar_ui=False, cargar_datos_iniciales=True)

    def _crear_interfaz(self):
        main_container = tb.Frame(self.root, padding=20)
        main_container.pack(fill=BOTH, expand=YES)

        # Encabezado y estado de conexión
        header_frame = tb.Frame(main_container)
        header_frame.pack(fill=X, pady=(0, 15))

        title_box = tb.Frame(header_frame)
        title_box.pack(side=LEFT, fill=X, expand=YES)

        tb.Label(
            title_box,
            text="Agente Inteligente de Climatización",
            font=("Helvetica", 18, "bold"),
            bootstyle="light"
        ).pack(anchor=W)

        tb.Label(
            title_box,
            text="Agente Reactivo Simple con inserción directa en Clúster MongoDB Atlas",
            font=("Helvetica", 10),
            bootstyle="secondary"
        ).pack(anchor=W)

        status_box = tb.Frame(header_frame)
        status_box.pack(side=RIGHT, padx=5)

        self.lbl_status = tb.Label(
            status_box,
            textvariable=self.var_status_cluster,
            font=("Helvetica", 10, "bold"),
            bootstyle="warning-inverse",
            padding=(12, 6)
        )
        self.lbl_status.pack(side=RIGHT)

        # Panel principal de 2 columnas
        body_frame = tb.Frame(main_container)
        body_frame.pack(fill=BOTH, expand=YES, pady=(0, 15))
        body_frame.columnconfigure(0, weight=5)
        body_frame.columnconfigure(1, weight=5)
        body_frame.rowconfigure(0, weight=1)

        # Columna izquierda: Sensores y entradas
        left_col = tb.Frame(body_frame)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        card_sensores = tb.Labelframe(
            left_col,
            text=" Percepción del Entorno (Sensores) ",
            padding=15,
            bootstyle="primary"
        )
        card_sensores.pack(fill=X, pady=(0, 12))

        tb.Label(card_sensores, text="Alumno / Operador:", font=("Helvetica", 10, "bold")).pack(anchor=W, pady=(0, 3))
        tb.Entry(card_sensores, textvariable=self.var_alumno, font=("Helvetica", 10), bootstyle="primary").pack(fill=X, pady=(0, 12))

        temp_header = tb.Frame(card_sensores)
        temp_header.pack(fill=X, pady=(0, 2))
        tb.Label(temp_header, text="Temperatura (°C):", font=("Helvetica", 10, "bold")).pack(side=LEFT)
        self.lbl_temp_val = tb.Label(temp_header, text=f"{self.var_temp.get():.1f} °C", font=("Helvetica", 10, "bold"), bootstyle="info")
        self.lbl_temp_val.pack(side=RIGHT)

        slider_temp = tb.Scale(
            card_sensores,
            from_=0.0,
            to=50.0,
            variable=self.var_temp,
            command=self._on_temp_slide,
            bootstyle="info"
        )
        slider_temp.pack(fill=X, pady=(0, 12))

        hum_header = tb.Frame(card_sensores)
        hum_header.pack(fill=X, pady=(0, 2))
        tb.Label(hum_header, text="Humedad Relativa (%):", font=("Helvetica", 10, "bold")).pack(side=LEFT)
        self.lbl_hum_val = tb.Label(hum_header, text=f"{self.var_hum.get():.1f} %", font=("Helvetica", 10, "bold"), bootstyle="primary")
        self.lbl_hum_val.pack(side=RIGHT)

        slider_hum = tb.Scale(
            card_sensores,
            from_=0.0,
            to=100.0,
            variable=self.var_hum,
            command=self._on_hum_slide,
            bootstyle="primary"
        )
        slider_hum.pack(fill=X, pady=(0, 15))

        btn_box = tb.Frame(card_sensores)
        btn_box.pack(fill=X)

        self.btn_evaluar = tb.Button(
            btn_box,
            text="Evaluar y Guardar en Clúster",
            command=self._evaluar_y_guardar_async,
            bootstyle="success",
            width=28
        )
        self.btn_evaluar.pack(fill=X, pady=(0, 8))

        btn_box_sub = tb.Frame(btn_box)
        btn_box_sub.pack(fill=X)

        tb.Button(
            btn_box_sub,
            text="Valores Aleatorios",
            command=self._simular_valores_aleatorios,
            bootstyle="secondary-outline"
        ).pack(side=LEFT, fill=X, expand=YES, padx=(0, 4))

        tb.Button(
            btn_box_sub,
            text="Probar Conexión",
            command=lambda: self._probar_conexion_async(notificar_ui=True),
            bootstyle="info-outline"
        ).pack(side=RIGHT, fill=X, expand=YES, padx=(4, 0))

        # Información de conexión
        card_info = tb.Labelframe(
            left_col,
            text=" Parámetros del Clúster ",
            padding=12,
            bootstyle="secondary"
        )
        card_info.pack(fill=X)

        db_str = f"Base: {self.mongo.db_name or 'N/A'}  |  Colección: {self.mongo.collection_name or 'N/A'}"
        cluster_str = f"Host: {self.mongo.cluster or 'N/A'}"
        tb.Label(card_info, text=db_str, font=("Helvetica", 9), bootstyle="secondary").pack(anchor=W)
        tb.Label(card_info, text=cluster_str, font=("Helvetica", 9), bootstyle="secondary").pack(anchor=W)

        # Columna derecha: Decisión y reglas
        right_col = tb.Frame(body_frame)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        card_decision = tb.Labelframe(
            right_col,
            text=" Decisión del Agente Reactivo ",
            padding=15,
            bootstyle="info"
        )
        card_decision.pack(fill=BOTH, expand=YES)

        tb.Label(
            card_decision,
            text="Regla Condición-Acción Aplicada:",
            font=("Helvetica", 10, "bold"),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 5))

        frame_decision_banner = tb.Frame(card_decision, padding=12)
        frame_decision_banner.pack(fill=X, pady=(0, 15))

        self.lbl_decision_texto = tb.Label(
            frame_decision_banner,
            textvariable=self.var_decision,
            font=("Helvetica", 12, "bold"),
            wraplength=380,
            justify=CENTER
        )
        self.lbl_decision_texto.pack(pady=10)

        tb.Separator(card_decision, bootstyle="secondary").pack(fill=X, pady=10)

        tb.Label(
            card_decision,
            text="Metadatos del Documento Insertado:",
            font=("Helvetica", 10, "bold"),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 8))

        detail_grid = tb.Frame(card_decision)
        detail_grid.pack(fill=X)

        tb.Label(detail_grid, text="ID en MongoDB:", font=("Helvetica", 9, "bold")).grid(row=0, column=0, sticky=W, pady=3)
        self.lbl_id_mongo = tb.Label(detail_grid, textvariable=self.var_ultimo_id, font=("Courier", 9), bootstyle="success")
        self.lbl_id_mongo.grid(row=0, column=1, sticky=W, padx=(10, 0), pady=3)

        tb.Label(detail_grid, text="Hora de Registro:", font=("Helvetica", 9, "bold")).grid(row=1, column=0, sticky=W, pady=3)
        tb.Label(detail_grid, textvariable=self.var_ultima_hora, font=("Helvetica", 9), bootstyle="light").grid(row=1, column=1, sticky=W, padx=(10, 0), pady=3)

        tb.Separator(card_decision, bootstyle="secondary").pack(fill=X, pady=10)
        tb.Label(card_decision, text="Tabla de Reglas:", font=("Helvetica", 9, "bold"), bootstyle="secondary").pack(anchor=W, pady=(0, 4))

        reglas_text = (
            "- Temp > 30°C y Hum > 70% -> Aire Acondicionado (Deshumidificador)\n"
            "- Temp > 30°C -> Ventilador\n"
            "- Temp < 18°C -> Calefacción\n"
            "- Otra condición -> Mantener sistema apagado"
        )
        tb.Label(card_decision, text=reglas_text, font=("Helvetica", 8), justify=LEFT, bootstyle="secondary").pack(anchor=W)

        # Historial de registros
        history_frame = tb.Labelframe(
            main_container,
            text=" Historial de Registros en el Clúster MongoDB ",
            padding=10,
            bootstyle="dark"
        )
        history_frame.pack(fill=BOTH, expand=YES)

        hist_top = tb.Frame(history_frame)
        hist_top.pack(fill=X, pady=(0, 6))

        tb.Button(
            hist_top,
            text="Actualizar del Clúster",
            command=self._cargar_historial_cluster_async,
            bootstyle="secondary"
        ).pack(side=LEFT, padx=(0, 5))

        tb.Button(
            hist_top,
            text="Limpiar Tabla",
            command=self._limpiar_tabla,
            bootstyle="secondary-link"
        ).pack(side=LEFT)

        tree_container = tb.Frame(history_frame)
        tree_container.pack(fill=BOTH, expand=YES)

        columnas = ("id", "fecha", "alumno", "temp", "hum", "accion")
        self.tree = tb.Treeview(
            tree_container,
            columns=columnas,
            show="headings",
            bootstyle="primary",
            height=7
        )

        self.tree.heading("id", text="ID MongoDB", anchor=W)
        self.tree.heading("fecha", text="Fecha y Hora", anchor=CENTER)
        self.tree.heading("alumno", text="Alumno / Autor", anchor=CENTER)
        self.tree.heading("temp", text="Temp (°C)", anchor=CENTER)
        self.tree.heading("hum", text="Humedad (%)", anchor=CENTER)
        self.tree.heading("accion", text="Acción Decidida", anchor=W)

        self.tree.column("id", width=190, stretch=False)
        self.tree.column("fecha", width=145, stretch=False)
        self.tree.column("alumno", width=110, stretch=False)
        self.tree.column("temp", width=85, stretch=False)
        self.tree.column("hum", width=95, stretch=False)
        self.tree.column("accion", width=340, stretch=True)

        scrollbar = tb.Scrollbar(tree_container, orient=VERTICAL, command=self.tree.yview, bootstyle="round")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

    def _on_temp_slide(self, val):
        self.lbl_temp_val.config(text=f"{float(val):.1f} °C")

    def _on_hum_slide(self, val):
        self.lbl_hum_val.config(text=f"{float(val):.1f} %")

    def _simular_valores_aleatorios(self):
        temp_rand = round(random.uniform(12.0, 38.0), 1)
        hum_rand = round(random.uniform(30.0, 90.0), 1)

        self.var_temp.set(temp_rand)
        self.var_hum.set(hum_rand)
        self._on_temp_slide(temp_rand)
        self._on_hum_slide(hum_rand)

    def _limpiar_tabla(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _probar_conexion_async(self, notificar_ui=True, cargar_datos_iniciales=False):
        self.lbl_status.config(bootstyle="warning-inverse")
        self.var_status_cluster.set("Conectando a Atlas...")

        def tarea():
            ok = self.mongo.connect()
            self.root.after(0, lambda: self._actualizar_estado_conexion(ok, notificar_ui, cargar_datos_iniciales))

        threading.Thread(target=tarea, daemon=True).start()

    def _actualizar_estado_conexion(self, ok: bool, notificar_ui: bool, cargar_datos_iniciales: bool):
        if ok:
            self.lbl_status.config(bootstyle="success-inverse")
            self.var_status_cluster.set(f"Clúster Conectado ({self.mongo.db_name}.{self.mongo.collection_name})")
            if notificar_ui:
                Messagebox.show_info(
                    f"Conexión exitosa a MongoDB Atlas.\n\nBase de datos: {self.mongo.db_name}\nColección: {self.mongo.collection_name}",
                    title="Clúster MongoDB"
                )
            if cargar_datos_iniciales:
                self._cargar_historial_cluster_async()
        else:
            self.lbl_status.config(bootstyle="danger-inverse")
            self.var_status_cluster.set("Error al conectar con Atlas")
            if notificar_ui:
                Messagebox.show_error(
                    f"No se pudo conectar a MongoDB Atlas.\n\nError: {self.mongo.last_error}",
                    title="Error de Conexión"
                )

    def _evaluar_y_guardar_async(self):
        alumno = self.var_alumno.get().strip() or "Manuel"
        temp = self.var_temp.get()
        hum = self.var_hum.get()

        self.agente.percibir(temp, hum)
        accion = self.agente.tomar_decision()
        estilo = self.agente.obtener_estilo_accion()

        self.var_decision.set(accion)
        self.lbl_decision_texto.config(bootstyle=estilo)

        self.btn_evaluar.config(text="Insertando en Clúster...", state=DISABLED)

        def tarea_insercion():
            try:
                nuevo_id = self.mongo.insert_lectura(alumno, temp, hum, accion)
                self.root.after(0, lambda: self._on_insercion_exitosa(nuevo_id, alumno, temp, hum, accion))
            except Exception as e:
                self.root.after(0, lambda: self._on_insercion_error(str(e)))

        threading.Thread(target=tarea_insercion, daemon=True).start()

    def _on_insercion_exitosa(self, nuevo_id: str, alumno: str, temp: float, hum: float, accion: str):
        self.btn_evaluar.config(text="Evaluar y Guardar en Clúster", state=NORMAL)
        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.var_ultimo_id.set(nuevo_id)
        self.var_ultima_hora.set(hora_actual)

        self.tree.insert(
            "",
            0,
            values=(nuevo_id, hora_actual, alumno, f"{temp:.1f}", f"{hum:.1f}", accion)
        )

        self.lbl_status.config(bootstyle="success-inverse")
        self.var_status_cluster.set(f"Insertado ID: {nuevo_id[:8]}... en Atlas")

    def _on_insercion_error(self, error_msg: str):
        self.btn_evaluar.config(text="Evaluar y Guardar en Clúster", state=NORMAL)
        self.lbl_status.config(bootstyle="danger-inverse")
        self.var_status_cluster.set("Error al insertar")
        Messagebox.show_error(
            f"Ocurrió un error al guardar en MongoDB Atlas:\n\n{error_msg}",
            title="Error al Insertar"
        )

    def _cargar_historial_cluster_async(self):
        def tarea():
            registros = self.mongo.obtener_ultimos_registros(limit=15)
            self.root.after(0, lambda: self._llenar_historial(registros))

        threading.Thread(target=tarea, daemon=True).start()

    def _llenar_historial(self, registros: list):
        self._limpiar_tabla()
        for doc in registros:
            doc_id = str(doc.get("_id", ""))
            fecha = doc.get("fecha_hora", "--")
            alumno = doc.get("alumno", "Manuel")
            temp = f"{float(doc.get('temperatura', 0)):.1f}" if "temperatura" in doc else "--"
            hum = f"{float(doc.get('humedad', 0)):.1f}" if "humedad" in doc else "--"
            accion = doc.get("accion", doc.get("mensaje", "--"))

            self.tree.insert(
                "",
                END,
                values=(doc_id, fecha, alumno, temp, hum, accion)
            )


if __name__ == "__main__":
    app_root = tb.Window(themename="darkly")
    app = AgenteClimatizacionGUI(app_root)
    app_root.mainloop()