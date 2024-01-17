import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import requests
import pickle
import plotly.express as px

#Funciones para crear los nuevos links de las imágenes
def agregar_ceros(numero):
    numero_str = str(numero)
    
    if len(numero_str) < 6:
        ceros_faltantes = 6 - len(numero_str)
        numero_str = '0' * ceros_faltantes + numero_str
    
    return numero_str

def url_rewrite(row):
    url = row['Photo'].split('.org/players/')[0]
    id_jugador = agregar_ceros(str(row['ID']))
    new_url = f'{url}.net/players/{id_jugador[:3]}/{id_jugador[3:]}/19_60.png'
    return new_url

def select_columns(selected_traits):
    columns = []
    for trait in selected_traits:
        columns.extend(traits[trait])
    return columns

BASIC_INFO = ['Age', 'Nationality', 'Overall', 'Potential', 'Club', 'Value', 'Wage', 'Preferred Foot']

st.set_page_config(page_title = "FIFA 19 Stats",
                   page_icon =  Image.open("sources/fifa19icon.png"),
                   layout =  "wide",
                   initial_sidebar_state = "collapsed")


@st.cache_data
def load_data():
    #Carga del DataFrame
    df = pd.read_csv('sources/fifa19.csv')
    df = df.drop('Unnamed: 0', axis =1)
    df['Photo'] = df.apply(url_rewrite, axis=1)

    #Carga del pickle con los traits
    with open('sources/traits.pkl', 'rb') as file:
        traits = pickle.load(file)

    return df, traits

df, traits = load_data()

def main():

    # Title
    st.title("Fifa 19 Stats DataSet")

    #Markdown de texto
    st.markdown("""Bienvenido al proyecto web experimental de Fifa 19.
                
Podrás conocer todas las estadísticas, datos y curiosidades
de tus jugadores y equipos favoritos para el modo carrera de Fifa 19""")
    
    with st.expander(label="DataFrame", expanded=False):
        st.dataframe(df)

    st.markdown("## Encuentra las estadísticas y demás info del jugador o jugadores que necesites para tu club")
    
    tab1, tab2, tab3, tab4 = st.tabs(['Búsqueda por nombre o club', 'Búsqueda por posición', 'Búsqueda por ID', 'Comparador de Stats'])
# Busqueda de jugadores por nombre o club

    search = tab1.text_input(label="Busca el jugador que quieras por su nombre o el club donde juega",
                     max_chars=50,
                     placeholder="Nombre o Club")
    

    df_filtered = df[(df['Name'].str.lower().str.contains(search.lower())) | (df['Club'].str.lower().str.contains(search.lower()))]
    
    if search != "" and len(df_filtered) > 0:
        tab1.success(f"Siuuuuu. Se han encontrado resultados a tu búsqueda de {search}")
        with tab1.expander(label="Resultado de búsqueda", expanded=False):
            tab1.dataframe(df_filtered)

    elif search != "":
        tab1.warning(f"This is not a Siuuuuuu. No se han encontrado resultados para {search}:(")


# Búsqueda de jugadores por posición
    # Multiple Selection
    posiciones = list(df['Position'].unique())
    posicion = tab2.multiselect(label="Busca los jugadores para la posición que necesitas",
                              options=posiciones,
                              default=None)
    
    pos_image = Image.open("sources/fifa_positions.jpg")
    
    tab2.image(image=pos_image,
         caption="Position Chart",
         use_column_width=False)
    
    df_pos = df[df['Position'].isin(posicion)]

    if len(posicion) > 0:
            tab2.success(f"Siuuuuu. Se han encontrado resultados a tu búsqueda de {posicion}")
            with tab2.expander(label="Resultado de búsqueda", expanded=False):
                tab2.dataframe(df_pos)


# Fede esto es lo nuevo
    search_id = tab3.number_input(label="Busca al jugador que quieras por su ID",
                         min_value=0,
                         max_value=df['ID'].max(),
                         value=0,
                         step=1)
    

    df_new = df[df['ID'] == search_id]

    if len(df_new) > 0:
        
        player = df_new['Name'].values[0]

        with tab3:
            col1, col2 = st.columns([2, 8])

            col1.header(player)

            try:
                picture = df_new['Photo'].values[0]
                picture = Image.open(requests.get(picture, stream = True).raw)
                width, height = picture.size
                new_width = 150  # ajusta el nuevo ancho según tus necesidades
                w_percent = (new_width / width)
                new_height = int((height * float(w_percent)))
                picture = picture.resize((new_width, new_height))
                col1.image(image=picture,
                    caption=None,
                    use_column_width=False)
            
            except:
                tab3.info(f'La foto de {player} no está disponible.')

            df_new = df_new[BASIC_INFO].T
            df_new.columns = ['Player Info']       
            col2.table(df_new)

    else:
        tab3.warning('El ID del jugador que estás buscando no existe')


    tab4.markdown("## Comparador de estadísticas in-game de jugadores")

    # Visualizador y comparador de estadísticas de los jugadores por tipo de traits
    # Búsqueda de jugadores por posición
    # Multiple Selection
    players_compare = list(df['Name'].unique())
    players_select = tab4.multiselect(label="Busca el/los jugador(es) que quieras visualizar.",
                                options=players_compare,
                                default=None)
    
    traits_select = tab4.multiselect(label="Selecciona las estadísticas que quieras visualizar.",
                                options=traits.keys(),
                                default=None)
    
    df_compare = df[df['Name'].isin(players_select)]
    df_compare = df_compare.sort_values(by = ['Overall', 'Age'], ascending=[False, True])

    if tab4.button('Lanzar comparación'):
    
        if len(df_compare) > 0 and len(traits_select) > 0:

            tab4.success(f'Tu comparación ha sido exitosa.')

            selected_columns = select_columns(traits_select)
            df_compare = df_compare[['Name'] + BASIC_INFO + selected_columns]
            st.dataframe(df_compare)

            df_compare = pd.melt(df_compare, id_vars = 'Name', value_vars = selected_columns,
                                            var_name = 'Traits', value_name = 'Stats')

            fig = px.bar(df_compare, x='Traits', y='Stats', color='Name',
                        barmode='group',
                        text_auto = True, #Esto es para ponerle los valores a cada columna
                        #category_orders={'Traits': selected_columns}, por debajo lo ordena según se consiga columnas en el df, si se quiere cambiar el orden se pasa como diccionario
                        #color_discrete_sequence=px.colors.qualitative.Set1,
                        title='Comparador de Stats')
        
            tab4.plotly_chart(figure_or_data=fig, use_container_width=True)

    

if __name__ == "__main__":
    main()
