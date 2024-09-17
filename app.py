import os
import json
import pandas as pd
import geopandas as gpd
from collections import defaultdict
import csv
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, State, ctx
import pymysql
from collections import defaultdict
import requests
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
#from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
import random
from sqlalchemy import create_engine

# file_path = os.path.join(current_dir, 'merged_region_birth_country.csv')
# DATA_DIR = os.path.join(current_dir, 'data')

# current_dir = os.path.dirname(os.path.abspath(__file__))
# geojson_file = os.path.join(current_dir, 'LGA_polygon.geojson')
# with open(geojson_file, encoding='utf-8') as f:
#     geojson_data = json.load(f)

# Define your connection string
connection_string = (
    "mysql+pymysql://admin:password@database-main.cx2moqkoe6wp.ap-southeast-2.rds.amazonaws.com:3306/harmonyHub"
)
# Create an SQLAlchemy engine
engine = create_engine(connection_string)

conn = pymysql.connect(
        host = 'database-main.cx2moqkoe6wp.ap-southeast-2.rds.amazonaws.com',
        port = 3306,
        user = 'admin',
        password = 'password',
        db = 'harmonyHub'
        )

# Fetch data from the MySQL table
query = "SELECT * FROM merged_region_birth_country"
csv_data = pd.read_sql(query, engine)

# try:
#     csv_data = pd.read_csv(file_path, encoding='utf-8')
# except UnicodeDecodeError:
#     csv_data = pd.read_csv(file_path, encoding='ISO-8859-1')

# ---------------
url = 'https://github.com/saniyakolangde/Fire_Detection_CV/blob/main/LGA_polygon.geojson?raw=true'
response = requests.get(url)

if response.status_code == 200:
    geojson_data = response.json()
    # Now you can use `geojson_data` as needed
# ---------------

# Convert GeoJSON data to a GeoDataFrame
geo_data = gpd.GeoDataFrame.from_features(geojson_data['features'])

# Preprocess the names to match CSV data
geo_data['Council Region'] = geo_data['name'].str.replace('City of ', '').str.strip()

# Convert the CSV data to the appropriate format
csv_data = csv_data.melt(id_vars='Council Region', var_name='Country', value_name='Count')

# Merge CSV data with GeoDataFrame
merged_geo_data = geo_data.merge(csv_data, on='Council Region')

# Convert the "Count" column to a numeric type, and cast the wrong one to NaN
merged_geo_data['Count'] = pd.to_numeric(merged_geo_data['Count'], errors='coerce')

# Calculate the average for each country and sort by "Count" in descending order
merged_df = merged_geo_data.groupby('Country')['Count'].mean().reset_index()
merged_df = merged_df.sort_values(by='Count', ascending=False)

# rename columns so they show correctly on mouse hover
merged_geo_data = merged_geo_data.rename(columns={'name': 'City', 'Count': 'People'})

# replace zeros with NaN so LGA with no people aren't coloured on map
merged_geo_data.People.replace(0, np.nan, inplace=True)

# create map
map_fig = px.choropleth_mapbox(
    merged_geo_data, geojson=geojson_data, locations=merged_geo_data['City'],
    featureidkey="properties.name",  # This key matches the name property in the GeoJSON
    color='People', hover_name='Council Region',
    color_continuous_scale="Viridis",
    title='Regions with People from Selected Countries',
    mapbox_style="carto-positron", center={"lat": -37.8136, "lon": 144.9631}, zoom=8, opacity=0.8
)

map_fig.update_traces(
    marker_line_color='black',  # Darker border color
    marker_line_width=0.8  # Adjust border thickness
)

country_languages = {
    "Afghanistan": "Persian (excluding Dari)",
    "Iran": "Persian (excluding Dari)",
    "Myanmar": "",
    "Iraq": "Arabic",
    "Pakistan": "Urdu",
    "Thailand": "Thai",
    "Sri Lanka": "Sinhalese / Tamil",
    "Malaysia": "",
    "India": "Hindi",
    "Lebanon": "Arabic",
    "Turkey": "Turkish",
    "Cambodia": "Khmer",
    "Egypt": "Arabic",
    "Papua New Guinea": "",
    "Indonesia": "Indonesian"
}

# query3 = "SELECT * FROM demographics"
# demographics_df = pd.read_sql(query3, conn)
# demographics_df['Country of Birth'] = demographics_df['Country of Birth'].apply(lambda x: x.replace(' ', '_'))

# text = ' '.join(demographics_df['Country of Birth'].tolist())

# def random_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
#     hue = random.randint(0, 255) 
#     saturation = 100 
#     lightness = random.randint(10, 40)  # only darker colors
#     return f"hsl({hue}, {saturation}%, {lightness}%)"

# Generate the word cloud with additional spacing and styling
# wordcloud = WordCloud(
#     width=450,
#     height=250,
#     background_color='white',
#     collocations=False,  # no overlapping words
#     prefer_horizontal=1.0,  # horizontal words
#     margin=12,  # space between words
#     #contour_width=1,  # Add a slight contour around the words
#     #contour_color='black',  # Set contour color to black
#     max_font_size=50,  #  maximum font size
#     min_font_size=13,
#     relative_scaling=0.5,
#     color_func=random_color_func  # random color functio
# ).generate(text)


# buffer = io.BytesIO()
# wordcloud.to_image().save(buffer, format='PNG')
# buffer.seek(0)
# image_base64 = base64.b64encode(buffer.getvalue()).decode()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
# App layout
app.layout = html.Div([    
    html.Div([
        dcc.Dropdown(
            id='demo-dropdown',
            options=[{'label': country, 'value': country} for country in ['', 'Afghanistan', 'Iran', 'Myanmar', 'Iraq', 'Pakistan', 'Thailand',
                    'Sri Lanka', 'Malaysia', 'India', 'Lebanon', 'Turkey', 'Cambodia',
                    'Egypt', 'Papua New Guinea', 'Indonesia']],
            value='All'
        )], style={'width': '40%', 'marginRight': '20px'}),  # Dropdown width and margin to separate from the graph

    # html.Div([
    #     dcc.Graph(id='map', figure=map_fig)]),

    # html.Div([
    #     dcc.Loading(
    #         id="loading-spinner",
    #         type="circle",  # Choose spinner type: 'default', 'circle', 'dot', 'cube', etc.
    #         children=[dcc.Graph(id='map', figure=map_fig)],
    #         fullscreen=True  # This will show a full-screen spinner
    #     )
    # ]),

    html.Div([
    dcc.Loading(
        id="loading-spinner",
        type="circle",  # Choose spinner type
        children=[dcc.Graph(id='map', figure=map_fig)],
        fullscreen=True,  # Full-screen spinner
        style={
            'fontSize': '250px',  # Increase size of the spinner
            'transform': 'scale(2)',
            'color': '#112840',  # Darker color (Bootstrap dark color)
            'display': 'flex',  # Use flex to center the spinner
            'alignItems': 'center',  # Center vertically
            'justifyContent': 'center'  # Center horizontally
        }
    )
]),

    
    dbc.Modal([
        dbc.ModalHeader("Details"),
        dbc.ModalBody([
            html.Div(id='total-count', style={'fontSize': 15}),
            html.Div(id='city-count', style={'fontSize': 15}),
            dcc.Graph(id='language-pie-chart'),
            html.Div(id='language-tip', style={'fontSize': 15}),
        ]),
        dbc.ModalFooter(
            dbc.Button("ok", id="close", className="ml-auto")
        )
    ], id="info-modal", is_open=False),
])

@app.callback(
    Output("info-modal", "is_open"),
    [Input("map", "clickData"), Input("close", "n_clicks")],
    [State("info-modal", "is_open")]
)
def toggle_modal(clickData, close_clicks, is_open):
    if clickData or close_clicks:
        return not is_open
    return is_open

@app.callback(
    Output('map', 'figure'),
    Input('demo-dropdown', 'value')
)
def update_map(value):
    if value:
        selected_country = value
        filtered_geo_data = merged_geo_data[merged_geo_data['Country'].str.title() == selected_country]
        map_fig = px.choropleth_mapbox(
            filtered_geo_data, geojson=geojson_data, locations=filtered_geo_data['City'],
            featureidkey="properties.name",
            color='People', hover_name='Council Region',
            color_continuous_scale="Viridis",
            title=f'Regions with People from {selected_country}',
            mapbox_style="carto-positron", center={"lat": -37.8136, "lon": 144.9631}, zoom=8, opacity=0.8
        )

        if filtered_geo_data.empty:
            # Handle the case where there is no data to display
            return px.choropleth_mapbox(
                merged_geo_data, geojson=geojson_data, locations=merged_geo_data['City'],
                featureidkey="properties.name",
                color='People', hover_name='Council Region',
                color_continuous_scale="Burg",
                title=f'No data available for {selected_country}',
                mapbox_style="carto-positron", center={"lat": -37.8136, "lon": 144.9631}, zoom=8, opacity=0.8
            )

    else:
        # Default to showing all regions
        map_fig = px.choropleth_mapbox(
            merged_geo_data, geojson=geojson_data, locations=merged_geo_data['City'],
            featureidkey="properties.name",
            color='People', hover_name='Council Region',
            color_continuous_scale="Viridis",
            title='Regions with People from Selected Countries',
            mapbox_style="carto-positron", center={"lat": -37.8136, "lon": 144.9631}, zoom=8, opacity=0.8
        )

    map_fig.update_traces(
        marker_line_color='black',  # Darker border color
        marker_line_width=0.8,  # Adjust border thickness
        hovertemplate='<b>%{hovertext}</b><br>Count: %{z}<br>Click for more information.<extra></extra>',
    )

    return map_fig

@app.callback(
    [Output('language-pie-chart', 'figure'),
     Output('total-count', 'children'),
     Output('city-count', 'children'),
     Output('language-tip', 'children')],
    [Input('map', 'clickData'),
     Input('demo-dropdown', 'value')]
)
def update_pie_chart(clickData, selected_country):
    if clickData:
        selected_region = clickData['points'][0]['hovertext']
        top_languages = get_top_five_language(selected_region, selected_country)
        print(top_languages)

        filtered_data = csv_data[(csv_data['Country'] == selected_country) & (csv_data['Council Region'] == selected_region)]
        
        csv_data['Count'] = pd.to_numeric(csv_data['Count'], errors='coerce')

        total_count = csv_data[csv_data['Country'] == selected_country]['Count'].sum()
        city_count = filtered_data['Count'].sum()

        total_text = f"Total number of people from {selected_country} in Victoria: {int(total_count)}"
        city_text = f"Total number of people from {selected_country} in {selected_region}: {int(city_count)}"

        language_total_count = sum(lang['count'] for lang in top_languages)

        tip_text = []
        for lang in top_languages:
            percentage = (lang['count'] / language_total_count) * 100
            if percentage < 1:
                tip_text.append(f"There are {lang['count']} {lang['language']} speaking people in {selected_region}")

        if not top_languages:
            return {
                "data": [{
                    "type": "pie",
                    "labels": [],
                    "values": []
                }],
                "layout": {
                    "title": f"No data available for {selected_region}"
                }
            }, total_text, city_text, "; ".join(tip_text)

        labels = [item['language'] for item in top_languages]
        values = [item['count'] for item in top_languages]

        return {
            "data": [{
                "type": "pie",
                "labels": labels,
                "values": values
            }],
            "layout": {
                "title": f"Top 5 Languages in {selected_region} (excluding English)"
            }
        }, total_text, city_text, "; ".join(tip_text)
    else:
        return {
            "data": [{
                "type": "pie",
                "labels": [],
                "values": []
            }],
            "layout": {
                "title": "Click on a region to see language distribution"
            }
        },  "Total Count: -", "City Count: -", ""

# def get_top_five_language(region_name):
#     file_path = os.path.join('region_languages', f"{region_name.replace(' ', '_')}.csv")
    
#     if not os.path.isfile(file_path):
#         return []

#     try:
#         language_counts = defaultdict(int)
        
#         with open(file_path, mode='r', newline='', encoding='utf-8') as file:
#             reader = csv.reader(file)
            
#             for row in reader:
#                 if len(row) < 2:
#                     continue
                
#                 language = row[0].strip()
#                 try:
#                     count = int(row[1].strip())
#                 except ValueError:
#                     continue
                
#                 if "Other(c)" in language or "Other(d)" in language or "Other(e)" in language or "Total" in language:
#                     continue
                
#                 language_counts[language] += count
        
#         sorted_languages = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
#         top_five = sorted_languages[:5]
        
#         return [{"language": language, "count": count} for language, count in top_five]
#     except Exception as e:
#         raise RuntimeError(f"Error processing data: {e}")

def str_2_int(number_str):
    # Remove the comma
    number_str = number_str.replace(',', '')
    # Convert to an integer
    return int(number_str)

def get_country_language(country_name, country_languages):
    return country_languages.get(country_name, "")

def get_top_five_language(region_name, country_name):
    # Load the CSV file into a DataFrame
    #file_path = 'merged_region_language.csv'
    
    try:
        country_language = get_country_language(country_name, country_languages)
        # Read the CSV file
        #df = pd.read_csv(file_path)
        # Fetch data from the MySQL table
        query2 = "SELECT * FROM merged_region_language"
        df = pd.read_sql(query2, engine)
        
        # Filter the DataFrame to get the row for the specified region
        region_row = df[df['Region'].str.strip().str.lower() == region_name.strip().lower()]
        
        if region_row.empty:
            return []

        # Drop the region_name column to focus on language columns
        language_data = region_row.drop(columns=['Region'])

        # Convert the data to a dictionary where keys are languages and values are counts
        language_counts = defaultdict(int)
        for language, count in language_data.items():
            try:
                count = int(region_row[language].values[0])
            except ValueError:
                continue
            
            # Skip "Other" categories and "Total"
            # if "Other(c)" in language or "Other(d)" in language or "Other(e)" in language or "Total" in language:
            #     continue
            
            language_counts[language] += count
        
        # Sort the languages by count in descending order
        sorted_languages = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return the top five languages as a list of dictionaries
        top_five = sorted_languages[:5]

        # Check if the country language is not in the top five
        if country_language and not any(
                language == country_language for language, _ in top_five):
            if top_five:
                # Replace the last language with the country language
                top_five[-1] = (
                country_language, language_counts.get(country_language, 0))
            else:
                # If there are fewer than 5 languages, just add the country language
                top_five = [(country_language,
                             language_counts.get(country_language, 0))]

        return [{"language": language, "count": count} for language, count in top_five]

    except Exception as e:
        raise RuntimeError(f"Error processing data: {e}")

if __name__ == '__main__':
    app.run_server(debug=True)
