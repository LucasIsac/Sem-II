# system_dashboard.py - Dashboard visual de recursos del sistema
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from tools import system_manager
import time

def create_gauge_chart(value, title, color_good="green", color_warning="yellow", color_critical="red"):
    """Crea un gráfico de gauge para mostrar porcentajes"""
    
    # Determinar color basado en el valor
    if value < 60:
        color = color_good
    elif value < 85:
        color = color_warning
    else:
        color = color_critical
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 16}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 60], 'color': 'lightgreen'},
                {'range': [60, 85], 'color': 'lightyellow'},
                {'range': [85, 100], 'color': 'lightcoral'}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}}))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def get_recommendations(cpu_percent, memory_percent, disk_percent):
    """Genera recomendaciones basadas en el uso de recursos"""
    recommendations = []
    
    # Recomendaciones de CPU
    if cpu_percent > 90:
        recommendations.append("🔥 **CPU Crítico**: Cierra programas innecesarios o reinicia aplicaciones que consuman mucho procesador")
    elif cpu_percent > 75:
        recommendations.append("⚠️ **CPU Alto**: Considera cerrar algunas aplicaciones en segundo plano")
    elif cpu_percent < 30:
        recommendations.append("✅ **CPU Óptimo**: Rendimiento excelente del procesador")
    
    # Recomendaciones de Memoria
    if memory_percent > 90:
        recommendations.append("🔥 **Memoria Crítica**: Cierra aplicaciones inmediatamente o reinicia el sistema")
    elif memory_percent > 80:
        recommendations.append("⚠️ **Memoria Alta**: Libera memoria cerrando pestañas del navegador o programas no esenciales")
    elif memory_percent < 50:
        recommendations.append("✅ **Memoria Óptima**: Uso de RAM saludable")
    
    # Recomendaciones de Disco
    if disk_percent > 95:
        recommendations.append("🔥 **Disco Crítico**: Libera espacio urgentemente eliminando archivos temporales o programas no usados")
    elif disk_percent > 85:
        recommendations.append("⚠️ **Disco Alto**: Considera limpiar archivos temporales, papelera o mover archivos a almacenamiento externo")
    elif disk_percent < 70:
        recommendations.append("✅ **Disco Óptimo**: Espacio en disco saludable")
    
    # Recomendaciones generales
    if cpu_percent > 80 and memory_percent > 80:
        recommendations.append("💡 **Sugerencia**: El sistema está sobrecargado. Considera reiniciar para liberar recursos")
    
    if len(recommendations) == 0:
        recommendations.append("🎉 **¡Excelente!** Tu sistema está funcionando de manera óptima")
    
    return recommendations

def show_system_dashboard():
    """Muestra el dashboard completo de recursos del sistema"""
    
    st.title("📊 Dashboard de Recursos del Sistema")
    
    # Obtener datos del sistema
    with st.spinner("Obteniendo información del sistema..."):
        system_info = system_manager.get_system_resources()
    
    if not system_info["success"]:
        st.error(f"Error al obtener recursos: {system_info['message']}")
        return
    
    details = system_info["details"]
    
    # Extraer valores
    cpu_percent = details["cpu"]["percent"]
    memory_percent = details["memory"]["percent"] 
    disk_percent = details["disk"]["percent"]
    
    # Crear layout de 3 columnas para los gauges
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cpu_fig = create_gauge_chart(cpu_percent, "CPU (%)")
        st.plotly_chart(cpu_fig, use_container_width=True)
    
    with col2:
        memory_fig = create_gauge_chart(memory_percent, "Memoria (%)")
        st.plotly_chart(memory_fig, use_container_width=True)
    
    with col3:
        disk_fig = create_gauge_chart(disk_percent, "Disco (%)")
        st.plotly_chart(disk_fig, use_container_width=True)
    
    # Información detallada
    st.markdown("---")
    st.subheader("📋 Información Detallada")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔧 CPU")
        st.metric("Uso Actual", f"{cpu_percent}%")
        st.metric("Núcleos", details["cpu"]["cores"])
        if details["cpu"]["frequency"] != "N/A":
            st.metric("Frecuencia", f"{details['cpu']['frequency']:.1f} MHz")
    
    with col2:
        st.markdown("### 🧠 Memoria")
        st.metric("Uso", f"{memory_percent}%")
        st.metric("Total", details["memory"]["total"])
        st.metric("Disponible", details["memory"]["available"])
        st.metric("En Uso", details["memory"]["used"])
    
    with col3:
        st.markdown("### 💾 Disco")
        st.metric("Uso", f"{disk_percent}%")
        st.metric("Total", details["disk"]["total"])
        st.metric("Libre", details["disk"]["free"])
        st.metric("Usado", details["disk"]["used"])
    
    # Gráfico de resumen
    st.markdown("---")
    st.subheader("📈 Resumen Visual")
    
    # Crear gráfico de barras
    resources = ['CPU', 'Memoria', 'Disco']
    values = [cpu_percent, memory_percent, disk_percent]
    colors = []
    
    for val in values:
        if val < 60:
            colors.append('green')
        elif val < 85:
            colors.append('orange')
        else:
            colors.append('red')
    
    fig = px.bar(
        x=resources, 
        y=values,
        color=colors,
        color_discrete_map={'green': '#2E8B57', 'orange': '#FF8C00', 'red': '#DC143C'},
        title="Uso de Recursos del Sistema (%)",
        labels={'y': 'Porcentaje de Uso (%)', 'x': 'Recursos'}
    )
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Recomendaciones
    st.markdown("---")
    st.subheader("💡 Recomendaciones")
    
    recommendations = get_recommendations(cpu_percent, memory_percent, disk_percent)
    
    for i, rec in enumerate(recommendations, 1):
        st.markdown(f"{i}. {rec}")
    
    # Estado general del sistema
    st.markdown("---")
    st.subheader("🏥 Estado General del Sistema")
    
    avg_usage = (cpu_percent + memory_percent + disk_percent) / 3
    
    if avg_usage < 60:
        st.success(f"🟢 **Sistema Saludable** - Uso promedio: {avg_usage:.1f}%")
        st.balloons()
    elif avg_usage < 80:
        st.warning(f"🟡 **Sistema Moderado** - Uso promedio: {avg_usage:.1f}%")
    else:
        st.error(f"🔴 **Sistema Sobrecargado** - Uso promedio: {avg_usage:.1f}%")
    
    # Botón para actualizar
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Actualizar Datos", type="primary", use_container_width=True):
            st.rerun()
    
    # Timestamp
    st.caption(f"📅 Última actualización: {time.strftime('%H:%M:%S - %d/%m/%Y')}")

# Función para integrar con el agente
def get_system_dashboard_response():
    """Función que el agente puede llamar para mostrar el dashboard"""
    system_info = system_manager.get_system_resources()
    
    if not system_info["success"]:
        return f"Error al obtener recursos del sistema: {system_info['message']}"
    
    details = system_info["details"]
    cpu_percent = details["cpu"]["percent"]
    memory_percent = details["memory"]["percent"] 
    disk_percent = details["disk"]["percent"]
    
    # Generar recomendaciones
    recommendations = get_recommendations(cpu_percent, memory_percent, disk_percent)
    
    response = f"""📊 **Estado Actual del Sistema:**

🔧 **CPU**: {cpu_percent}% ({details['cpu']['cores']} núcleos)
🧠 **Memoria**: {memory_percent}% ({details['memory']['used']} de {details['memory']['total']} usado)
💾 **Disco**: {disk_percent}% ({details['disk']['used']} de {details['disk']['total']} usado)

💡 **Recomendaciones:**
"""
    
    for i, rec in enumerate(recommendations, 1):
        response += f"\n{i}. {rec.replace('**', '').replace('🔥', '🔥').replace('⚠️', '⚠️').replace('✅', '✅').replace('💡', '💡').replace('🎉', '🎉')}"
    
    avg_usage = (cpu_percent + memory_percent + disk_percent) / 3
    if avg_usage < 60:
        response += f"\n\n🟢 **Estado General**: Sistema saludable (uso promedio: {avg_usage:.1f}%)"
    elif avg_usage < 80:
        response += f"\n\n🟡 **Estado General**: Sistema moderadamente cargado (uso promedio: {avg_usage:.1f}%)"
    else:
        response += f"\n\n🔴 **Estado General**: Sistema sobrecargado (uso promedio: {avg_usage:.1f}%)"
    
    return response

# Para testing directo
if __name__ == "__main__":
    show_system_dashboard()