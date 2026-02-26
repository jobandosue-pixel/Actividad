import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Gestor Metales/Unican", layout="centered")

DB_FILE = "actividades.csv"
SIG_DIR = "firmas"
if not os.path.exists(SIG_DIR): os.makedirs(SIG_DIR)

# --- INICIALIZACIÓN DE ESTADOS ---
if 'indice_edit' not in st.session_state: st.session_state.indice_edit = None
if 'reset_canvas' not in st.session_state: st.session_state.reset_canvas = 0

# --- LÓGICA DE DATOS ---
def cargar_datos():
    columnas = ["Fecha", "Hora", "Empresa", "Actividad", "Categoría", "Estado", "Observaciones", "Firma_Path"]
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            for col in columnas:
                if col not in df.columns: df[col] = ""
            df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
            return df
        except:
            return pd.DataFrame(columns=columnas)
    return pd.DataFrame(columns=columnas)

def cb_limpiar():
    st.session_state.indice_edit = None
    st.session_state.reset_canvas += 1
    if "tabla_actividades" in st.session_state:
        st.session_state.tabla_actividades = {"selection": {"rows": []}}

def enviar_reporte_html_semaforo(destinatario, asunto, df_reporte):
    try:
        EMAIL_EMISOR = "jobandosue@gmail.com"
        EMAIL_PASSWORD = "osqqdpnuixkguctr" 
        msg = MIMEMultipart()
        msg['From'] = EMAIL_EMISOR
        msg['To'] = destinatario
        msg['Subject'] = asunto

        df_correo = df_reporte.drop(columns=['Firma_Path'], errors='ignore')
        
        filas_html = ""
        for i, (_, row) in enumerate(df_correo.iterrows()):
            est = str(row['Estado']).strip()
            bg_color = "#e2e3e5"; text_color = "#383d41"
            if est == "Finalizado": bg_color = "#d4edda"; text_color = "#155724"
            elif est == "En Proceso": bg_color = "#fff3cd"; text_color = "#856404"
            elif est == "Pendiente": bg_color = "#f8d7da"; text_color = "#721c24"
            
            row_bg = "#ffffff" if i % 2 == 0 else "#f9f9f9"
            
            filas_html += f"<tr style='background-color: {row_bg}; border: 1px solid #dddddd;'>"
            for col_name, val in row.items():
                if col_name == "Estado":
                    filas_html += f"""<td style='padding: 12px; border: 1px solid #dddddd; text-align: center;'>
                        <span style='background-color: {bg_color}; color: {text_color}; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; border: 1px solid rgba(0,0,0,0.1);'>
                            {val}
                        </span></td>"""
                else:
                    filas_html += f"<td style='padding: 12px; border: 1px solid #dddddd; color: #555;'>{val}</td>"
            filas_html += "</tr>"

        html_table = f"""
        <div style='overflow-x:auto;'>
            <table style='border-collapse: collapse; width: 100%; font-family: sans-serif; font-size: 14px; border: 1px solid #dddddd;'>
                <thead>
                    <tr style='background-color: #009879; color: #ffffff; text-align: left;'>
                        {''.join([f"<th style='padding: 15px; border: 1px solid #007f65;'>{col}</th>" for col in df_correo.columns])}
                    </tr>
                </thead>
                <tbody>{filas_html}</tbody>
            </table>
        </div>
        """
        cuerpo_html = f"<html><body>{html_table}</body></html>"
        msg.attach(MIMEText(cuerpo_html, 'html'))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        server.sendmail(EMAIL_EMISOR, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error correo: {e}"); return False

df = cargar_datos()

# 2. INTERFAZ
st.title("📱 Mi Control Diario")

LISTA_EMPRESAS = ["Metales Flix", "Industrias Unican", "Otros"]
LISTA_CATS = ["Reunión", "Desarrollo", "Administrativo", "Personal", "Configuracion", "Arreglo", "Preventivo", "Correctivo"]

edit_idx = st.session_state.indice_edit

if edit_idx is not None and edit_idx < len(df):
    row = df.iloc[edit_idx]
    def_emp, def_act, def_cat, def_est, def_obs, path_firma = str(row['Empresa']), str(row['Actividad']), str(row['Categoría']), str(row['Estado']), str(row['Observaciones']), str(row['Firma_Path'])
    texto_boton = "🔄 ACTUALIZAR REGISTRO"
else:
    def_emp, def_act, def_cat, def_est, def_obs, path_firma = "Metales Flix", "", "Reunión", "Pendiente", "", ""
    texto_boton = "💾 GUARDAR NUEVO"

# --- FORMULARIO ---
with st.container(border=True):
    st.subheader("📝 Editar Registro" if edit_idx is not None else "➕ Nueva Actividad")
    
    id_ref = f"{edit_idx}_{st.session_state.reset_canvas}"
    
    empresa = st.selectbox("Empresa", LISTA_EMPRESAS, index=LISTA_EMPRESAS.index(def_emp) if def_emp in LISTA_EMPRESAS else 0, key=f"emp_{id_ref}")
    actividad = st.text_input("Actividad", value=def_act, key=f"act_{id_ref}")
    categoria = st.selectbox("Categoría", LISTA_CATS, index=LISTA_CATS.index(def_cat) if def_cat in LISTA_CATS else 0, key=f"cat_{id_ref}")
    estado = st.select_slider("Estado", options=["Pendiente", "En Proceso", "Finalizado"], value=def_est, key=f"est_{id_ref}")
    observaciones = st.text_area("Observaciones", value=def_obs, key=f"obs_{id_ref}")
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.write("🖼️ **Firma Actual**")
        if path_firma and os.path.exists(path_firma): st.image(path_firma, width=200)
        else: st.info("Sin firma")
    with c2:
        st.write("✍️ **Firma aquí**")
        # El cursor de dibujo por defecto en freedraw es una cruz de precisión
        canvas_result = st_canvas(
            stroke_width=3,
            stroke_color="#000000",
            background_color="#ffffff",
            height=150,
            drawing_mode="freedraw",
            key=f"canvas_{id_ref}",
            display_toolbar=True # Esto permite al usuario ver herramientas de dibujo
        )

    cols = st.columns([2, 1, 1]) if edit_idx is not None else st.columns([2, 2])
    with cols[0]:
        if st.button(texto_boton, width='stretch', type="primary"):
            if actividad:
                ruta_final = path_firma
                if canvas_result.json_data and len(canvas_result.json_data["objects"]) > 0:
                    nombre = f"sig_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    ruta_final = os.path.join(SIG_DIR, nombre)
                    Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').save(ruta_final)
                
                nueva_data = {
                    "Fecha": df.at[edit_idx, 'Fecha'] if edit_idx is not None else datetime.now().date(),
                    "Hora": df.at[edit_idx, 'Hora'] if edit_idx is not None else datetime.now().strftime("%H:%M:%S"),
                    "Empresa": empresa, "Actividad": actividad, "Categoría": categoria, 
                    "Estado": estado, "Observaciones": observaciones, "Firma_Path": ruta_final
                }
                if edit_idx is not None: df.iloc[edit_idx] = nueva_data
                else: df = pd.concat([df, pd.DataFrame([nueva_data])], ignore_index=True)
                df.to_csv(DB_FILE, index=False)
                st.toast("✅ Realizado"); cb_limpiar(); st.rerun()
            else: st.error("Falta Actividad")

    with cols[1]:
        if st.button("🧹 LIMPIAR", width='stretch'):
            cb_limpiar(); st.rerun()

    if edit_idx is not None:
        with cols[2]:
            if st.button("🗑️ ELIMINAR", width='stretch'):
                df = df.drop(edit_idx)
                df.to_csv(DB_FILE, index=False)
                st.toast("❌ Eliminado"); cb_limpiar(); st.rerun()

# 3. HISTORIAL
st.divider()
st.subheader("📊 Historial")
busqueda = st.text_input("🔍 Buscar...")
df_f = df.copy()
if busqueda:
    df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]

df_sorted = df_f.sort_index(ascending=False)
sel = st.dataframe(
    df_sorted, width='stretch', on_select="rerun", selection_mode="single-row",
    column_config={"Firma_Path": None, "Hora": None, "Observaciones": None},
    key="tabla_actividades"
)

if sel and "selection" in sel and len(sel["selection"]["rows"]) > 0:
    idx_real = df_sorted.index[sel["selection"]["rows"][0]]
    if st.session_state.indice_edit != idx_real:
        st.session_state.indice_edit = idx_real
        st.rerun()

# 4. REPORTE
st.divider()
with st.expander("📧 Generar Reporte"):
    f1 = st.date_input("Inicio", datetime.now())
    f2 = st.date_input("Fin", datetime.now())
    dest = st.text_input("Correo:")
    if st.button("ENVIAR TABLA", width='stretch'):
        mask = (df['Fecha'] >= f1) & (df['Fecha'] <= f2)
        repo = df.loc[mask].copy()
        if not repo.empty:
            if enviar_reporte_html_semaforo(dest, "Reporte de Actividades", repo):
                st.success("✅ Reporte enviado.")
        else: st.warning("No hay datos.")