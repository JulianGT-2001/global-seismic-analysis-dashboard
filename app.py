
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from scipy.stats import ttest_ind

file_path = './data/database.csv'

st.set_page_config(page_title='EDA Dashboard', layout='wide')
st.title('Perspectiva de la Actividad Sísmica Mundial (1965-2016)')

# Carga de datos
df = pd.read_csv(file_path, index_col='Date', parse_dates=True)

# Recuperar Date como columna
df = df.reset_index()

# Extraer año
df['Year'] = pd.to_datetime(df['Date'], errors='coerce').dt.year

# Sidebar - Filtros
with st.sidebar:
    st.header('Filtros')
    categoria = st.selectbox(
        'Selecciona categoría:',
        df['Type'].dropna().unique()
    )

    magnitud = st.slider(
        'Selecciona intervalo de magnitud:',
        min_value=float(df['Magnitude'].dropna().min()),
        max_value=float(df['Magnitude'].dropna().max()),
        value=(
            float(df['Magnitude'].dropna().min()),
            float(df['Magnitude'].dropna().max())
        )
    )

    df_filtrado = df[
        (df['Type'] == categoria) &
        (df['Magnitude'] >= magnitud[0]) &
        (df['Magnitude'] <= magnitud[1])
    ]

# Métricas
col1, col2, col3 = st.columns(3)

col1.metric('Registros', len(df_filtrado))

# Visualización
st.subheader('Cantidad de Sismos por Año')

sns.set_theme(style='whitegrid')

fig, ax = plt.subplots(figsize=(12, 5))

sns.histplot(
    data=df_filtrado.dropna(subset=['Year']),
    x='Year',
    ax=ax,
    binwidth=1,
    discrete=True,
    color='steelblue',
    edgecolor='white'
)

ax.set_title('Cantidad de Sismos Registrados por Año (1965-2016)')
ax.set_xlabel('Año')
ax.set_ylabel('Cantidad de sismos')
ax.set_xticks(range(1965, 2017, 2))
ax.tick_params(axis='x', rotation=45)

fig.tight_layout()

st.pyplot(fig)
plt.close(fig)

st.subheader('Ubicación Geográfica de los Sismos')

# 1. Limpieza: Eliminamos los registros que tengan coordenadas nulas
df_geo = df_filtrado.dropna(subset=['Latitude', 'Longitude'])

# 2. Inicializamos el mapa utilizando azulejos de Esri públicos para evitar requerir API keys de CartoDB
mapa_sismos = folium.Map(
    location=[0, 0],
    zoom_start=2,
    control_scale=True,
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
    attr='Esri, USGS, NOAA'
)

# 3. Creamos un clúster de marcadores para mejorar el rendimiento interactivo
marker_cluster = MarkerCluster().add_to(mapa_sismos)

# 4. Agregamos una muestra aleatoria de 2,000 sismos para balancear detalle y rendimiento
df_sample = df_geo.sample(n=min(2000, len(df_geo)), random_state=42)

for idx, row in df_sample.iterrows():
    # Crear la descripción emergente (popup) al hacer clic en cada marcador
    info_sismo = f"<b>Tipo:</b> {row['Type']}<br><b>Magnitud:</b> {row['Magnitude']}<br><b>Profundidad:</b> {row['Depth']} km"

    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(info_sismo, max_width=300)
    ).add_to(marker_cluster)

st_folium(
    mapa_sismos,
    width=None,
    height=550,
    use_container_width=True
)

st.subheader('Tendencia Temporal de la Magnitud Promedio de los Eventos Sísmicos')

fig, ax = plt.subplots(figsize=(12, 5))

tendencia_magnitud = df_filtrado.groupby('Year')['Magnitude'].mean().reset_index()
tendencia_magnitud.columns = ['Año', 'Magnitud Promedio']

plt.figure(figsize=(14, 5))

sns.lineplot(data=tendencia_magnitud, x='Año', y='Magnitud Promedio', marker='o', color='teal', linewidth=2, ax=ax)

ax.set_title('Tendencia Temporal de la Magnitud Promedio de los Eventos Sísmicos')
ax.set_xlabel('Año')
ax.set_ylabel('Magnitud Promedio')

st.pyplot(fig)
plt.close(fig)


# Validación
st.subheader('Comparación de la actividad sísmica')

st.write(
    "En esta sección se analiza si existen diferencias "
    "importantes en la magnitud de los terremotos y las "
    "explosiones nucleares registradas."
)

# Obtener los datos
terremotos = df_filtrado.loc[
    df_filtrado['Type'] == 'Earthquake', 'Magnitude'
].dropna()

explosiones = df_filtrado.loc[
    df_filtrado['Type'] == 'Nuclear Explosion', 'Magnitude'
].dropna()

# Nivel de confianza del 95 %
alpha = 0.05

# Comparación estadística
resultado = ttest_ind(
    terremotos,
    explosiones,
    equal_var=False
)

# Mostrar cantidades analizadas
col1, col2 = st.columns(2)

col1.metric('Terremotos analizados', len(terremotos))
col2.metric('Explosiones nucleares analizadas', len(explosiones))

# Mostrar resultados
st.divider()

if resultado.pvalue < alpha:
    st.success(
        "Se identificaron diferencias importantes entre "
        "las magnitudes de los dos tipos de eventos."
    )

    st.write(
        "Los resultados indican que las diferencias observadas "
        "son suficientemente claras para considerar que las "
        "magnitudes promedio de ambos grupos son distintas."
    )

else:
    st.info(
        "No se identificaron diferencias estadísticamente "
        "significativas entre las magnitudes de los dos grupos."
    )

    st.write(
        "Con la información analizada, no se cuenta con "
        "evidencia suficiente para afirmar que las magnitudes "
        "promedio de ambos grupos sean diferentes."
    )

st.subheader('Exploración de datos')

st.write(
    'Consulta los registros sísmicos y explora sus '
    'principales características según los filtros seleccionados.'
)

# 1. Buscador de registros
busqueda = st.text_input(
    'Buscar en los registros:',
    placeholder='Escribe una palabra, ubicación, fecha o tipo de evento...'
)

# 2. Copiar los datos filtrados
df_exploracion = df_filtrado.copy()

# 3. Aplicar búsqueda adicional
if busqueda:
    coincidencias = df_exploracion.astype(str).apply(
        lambda columna: columna.str.contains(
            busqueda,
            case=False,
            na=False
        )
    ).any(axis=1)

    df_exploracion = df_exploracion[coincidencias]

# 4. Calcular métricas principales
media_magnitud = df_exploracion['Magnitude'].mean()
desviacion_magnitud = df_exploracion['Magnitude'].std()
total_registros = len(df_exploracion)

# 5. Mostrar métricas
col1, col2, col3 = st.columns(3)

col1.metric(
    label='Magnitud promedio',
    value=f'{media_magnitud:.2f}' if pd.notna(media_magnitud) else 'N/D'
)


col2.metric(
    label='Desviación estándar',
    value=f'{desviacion_magnitud:.2f}' if pd.notna(desviacion_magnitud) else 'N/D'
)

col3.metric(
    label='Total de registros',
    value=f'{total_registros:,}'
)

st.divider()

st.markdown('### Registros sísmicos')

st.caption(
    f'Se encontraron {total_registros:,} registros '
    'que coinciden con los criterios seleccionados.'
)

st.dataframe(
    df_exploracion,
    use_container_width=True,
    hide_index=True,
    height=450,
    column_config={
        'Date': st.column_config.DateColumn(
            'Fecha del evento',
            format='DD/MM/YYYY'
        ),
        'Magnitude': st.column_config.NumberColumn(
            'Magnitud',
            format='%.2f'
        ),
        'Depth': st.column_config.NumberColumn(
            'Profundidad (km)',
            format='%.2f'
        ),
        'Latitude': st.column_config.NumberColumn(
            'Latitud',
            format='%.4f'
        ),
        'Longitude': st.column_config.NumberColumn(
            'Longitud',
            format='%.4f'
        )
    }
)

st.divider()

st.header("Hallazgos del análisis")

st.markdown("""
En esta sección se presentan los principales resultados del análisis
de los eventos sísmicos registrados alrededor del mundo entre 1965
y 2016. El propósito es comprender su comportamiento histórico,
identificar patrones relevantes y ofrecer información que facilite
la interpretación de estos fenómenos.
""")

# Se utiliza el conjunto de datos filtrado en el dashboard.
datos = df_filtrado.copy()

datos["Date"] = pd.to_datetime(datos["Date"], errors="coerce")
datos["Year"] = datos["Date"].dt.year

datos["Magnitude"] = pd.to_numeric(
    datos["Magnitude"], errors="coerce"
)

datos["Depth"] = pd.to_numeric(
    datos["Depth"], errors="coerce"
)

datos_validos = datos.dropna(subset=["Year", "Magnitude"])

if datos_validos.empty:
    st.warning(
        "No hay suficientes registros para presentar hallazgos. "
        "Modifica los filtros seleccionados."
    )

else:

    # --------------------------------------------------------
    # 2. Cálculo de los principales resultados
    # --------------------------------------------------------

    total_eventos = len(datos_validos)

    magnitud_promedio = datos_validos["Magnitude"].mean()

    magnitud_maxima = datos_validos["Magnitude"].max()

    anio_inicio = int(datos_validos["Year"].min())
    anio_fin = int(datos_validos["Year"].max())

    eventos_por_anio = (
        datos_validos.groupby("Year")
        .size()
        .sort_values(ascending=False)
    )

    anio_mas_eventos = int(eventos_por_anio.idxmax())
    cantidad_anio_maximo = int(eventos_por_anio.max())

    tipo_principal = datos_validos["Type"].value_counts()

    tipo_mas_frecuente = tipo_principal.index[0]
    cantidad_tipo_principal = int(tipo_principal.iloc[0])

    magnitud_por_tipo = (
        datos_validos.groupby("Type")["Magnitude"]
        .mean()
        .sort_values(ascending=False)
    )

    tipo_mayor_magnitud = magnitud_por_tipo.index[0]
    promedio_tipo_mayor = magnitud_por_tipo.iloc[0]

    # --------------------------------------------------------
    # 3. ¿Qué analicé?
    # --------------------------------------------------------

    st.subheader("1. ¿Qué analicé?")

    st.markdown(f"""
    Se estudió un conjunto de **{total_eventos:,} registros de eventos
    sísmicos** ocurridos en diferentes regiones del mundo entre
    {anio_inicio} y {anio_fin}.

    La información permite conocer cuándo ocurrieron estos eventos,
    dónde se localizaron, qué tipo de fenómeno se presentó, a qué
    profundidad se produjo y cuál fue su magnitud.

    El análisis busca comprender cómo se distribuyen los eventos
    sísmicos a lo largo del tiempo, cuáles son los tipos de eventos
    más frecuentes y qué diferencias existen en la intensidad
    registrada. Esta información permite construir una visión general
    del comportamiento histórico de la actividad sísmica mundial.
    """)

    # --------------------------------------------------------
    # 4. ¿Qué encontré?
    # --------------------------------------------------------

    st.subheader("2. ¿Qué encontré?")

    st.markdown(f"""
    Durante el periodo estudiado se identificaron **{total_eventos:,}
    eventos sísmicos**. Uno de los resultados más relevantes es que
    la distribución de estos fenómenos no es uniforme a lo largo
    del tiempo.

    El año **{anio_mas_eventos}** concentró la mayor cantidad de
    registros, con **{cantidad_anio_maximo:,} eventos**. Esto permite
    identificar periodos en los que se documentó una mayor actividad
    sísmica dentro del conjunto de información analizado.

    En cuanto a los tipos de eventos, **{tipo_mas_frecuente}** fue
    la categoría con mayor número de registros, representando
    {cantidad_tipo_principal:,} eventos.

    Por otra parte, la magnitud promedio de los eventos registrados
    fue de **{magnitud_promedio:.2f}**, mientras que el valor máximo
    observado alcanzó **{magnitud_maxima:.2f}**.

    Al comparar los diferentes tipos de fenómenos, se encontró que
    **{tipo_mayor_magnitud}** presentó la mayor magnitud promedio,
    con un valor de **{promedio_tipo_mayor:.2f}**.

    Estos resultados muestran que los eventos sísmicos presentan
    diferencias tanto en su frecuencia de aparición como en la
    intensidad registrada.
    """)

    # --------------------------------------------------------
    # 5. Visualización 1: Eventos a través del tiempo
    # --------------------------------------------------------

    st.markdown("#### ¿Cómo han cambiado los registros sísmicos a través de los años?")

    eventos_anuales = (
        datos_validos.groupby("Year")
        .size()
        .reset_index(name="Cantidad de eventos")
    )

    eventos_anuales["Año"] = eventos_anuales["Year"].astype(str)

    st.line_chart(
        eventos_anuales.set_index("Año")["Cantidad de eventos"],
        x_label="Año",
        y_label="Número de eventos registrados"
    )

    st.caption(
        "Esta gráfica muestra cuántos eventos sísmicos fueron "
        "registrados durante cada año del periodo analizado."
    )

    # --------------------------------------------------------
    # 6. Visualización 2: Magnitud por tipo de evento
    # --------------------------------------------------------

    st.markdown("#### ¿Qué intensidad promedio presenta cada tipo de evento?")

    comparacion_tipos = (
        datos_validos.groupby("Type")["Magnitude"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    comparacion_tipos.columns = [
        "Tipo de evento",
        "Magnitud promedio"
    ]

    st.bar_chart(
        comparacion_tipos.set_index("Tipo de evento"),
        x_label="Tipo de evento",
        y_label="Magnitud promedio registrada"
    )

    st.caption(
        "La comparación permite observar las diferencias en la "
        "magnitud promedio entre las distintas categorías de eventos."
    )

    # --------------------------------------------------------
    # 7. ¿Qué significa?
    # --------------------------------------------------------

    st.subheader("3. ¿Qué significa?")

    st.markdown(f"""
    Los resultados permiten comprender varios aspectos importantes
    del comportamiento sísmico:

    - **Concentración temporal:** el mayor número de registros en
      {anio_mas_eventos} indica que existió un periodo con más
      eventos documentados. Esto puede orientar investigaciones
      sobre la actividad sísmica de ese año, aunque no significa
      necesariamente que todos los años anteriores o posteriores
      hayan tenido menor actividad real.

    - **Predominio de un tipo de evento:** la frecuencia de
      {tipo_mas_frecuente} muestra que esta categoría ocupa un lugar
      importante dentro de los registros estudiados. Por tanto,
      merece especial atención al analizar el comportamiento
      histórico de los fenómenos.

    - **Diferencias en la intensidad:** los valores de magnitud
      permiten distinguir eventos de menor y mayor intensidad.
      Esto es relevante porque los fenómenos de mayor magnitud
      pueden representar mayores desafíos para las comunidades
      y las infraestructuras expuestas.

    - **Importancia de la información histórica:** conocer cuándo,
      dónde y con qué intensidad ocurrieron estos eventos permite
      identificar antecedentes que pueden servir de referencia
      para la planificación territorial y la preparación ante
      futuras emergencias.

    Es importante recordar que estos registros describen eventos
    históricos y no permiten predecir con exactitud cuándo o dónde
    ocurrirá un próximo terremoto.
    """)

    # --------------------------------------------------------
    # 8. ¿Qué se recomendaría?
    # --------------------------------------------------------

    st.subheader("4. ¿Qué se recomendaría?")

    st.markdown("""
    A partir de los resultados obtenidos, se plantean las siguientes
    recomendaciones:

    1. **Fortalecer la preparación ante emergencias:** utilizar los
       antecedentes sísmicos como referencia para revisar los
       protocolos de respuesta, evacuación y atención de desastres.

    2. **Priorizar el análisis de las zonas históricamente afectadas:**
       complementar los registros mundiales con información
       geográfica local para identificar comunidades e
       infraestructuras que requieren mayor atención.

    3. **Promover construcciones más seguras:** utilizar la información
       histórica como insumo para revisar las condiciones de
       infraestructura y el cumplimiento de las normas de
       construcción sismorresistente.

    4. **Mantener actualizados los registros:** incorporar nuevos
       eventos y mejorar la calidad de los datos para facilitar
       futuras investigaciones y comparaciones.

    5. **Mejorar la comunicación del riesgo:** presentar la información
       sísmica de manera clara y accesible para que las instituciones
       y la ciudadanía puedan comprender los riesgos y tomar
       decisiones informadas.

    Estas recomendaciones deben complementarse con estudios locales
    de amenaza, vulnerabilidad y exposición para orientar decisiones
    específicas.
    """)

    st.info(
        "Los hallazgos corresponden exclusivamente a los registros "
        "seleccionados mediante los filtros del dashboard. "
        "La información histórica no constituye una herramienta "
        "de predicción de terremotos."
    )