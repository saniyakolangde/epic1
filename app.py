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
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
import random

# current_dir = os.path.dirname(os.path.abspath(__file__))
# file_path = os.path.join(current_dir, 'merged_region_birth_country.csv')
# geojson_file = os.path.join(current_dir, 'LGA_polygon.geojson')
# DATA_DIR = os.path.join(current_dir, 'data')

conn = pymysql.connect(
        host = 'database-ta02.cx2moqkoe6wp.ap-southeast-2.rds.amazonaws.com',
        port = 3306,
        user = 'admin',
        password = 'password',
        db = 'main_project_database'
        )

# Fetch data from the MySQL table
query = "SELECT * FROM merged_region_birth_country"
csv_data = pd.read_sql(query, conn)

# try:
#     csv_data = pd.read_csv(file_path, encoding='utf-8')
# except UnicodeDecodeError:
#     csv_data = pd.read_csv(file_path, encoding='ISO-8859-1')

# with open(geojson_file, encoding='utf-8') as f:
#     geojson_data = json.load(f)

url = 'https://github.com/saniyakolangde/Fire_Detection_CV/blob/main/LGA_polygon.geojson?raw=true'
response = requests.get(url)

if response.status_code == 200:
    geojson_data = response.json()
    # Now you can use `geojson_data` as needed

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

# create map
map_fig = px.choropleth_mapbox(
    merged_geo_data, geojson=geojson_data, locations=merged_geo_data['name'],
    featureidkey="properties.name",  # This key matches the name property in the GeoJSON
    color='Count', hover_name='Council Region',
    color_continuous_scale="Viridis",
    title='Regions with People from Selected Countries',
    mapbox_style="carto-positron", center={"lat": -37.8136, "lon": 144.9631}, zoom=8, opacity=0.8
)

map_fig.update_traces(
    marker_line_color='black',  # Darker border color
    marker_line_width=0.8  # Adjust border thickness
)

query3 = "SELECT * FROM demographics"
demographics_df = pd.read_sql(query3, conn)
demographics_df['Country of Birth'] = demographics_df['Country of Birth'].apply(lambda x: x.replace(' ', '_'))

text = ' '.join(demographics_df['Country of Birth'].tolist())

def random_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    hue = random.randint(0, 255) 
    saturation = 100 
    lightness = random.randint(10, 40)  # only darker colors
    return f"hsl({hue}, {saturation}%, {lightness}%)"

# Generate the word cloud with additional spacing and styling
wordcloud = WordCloud(
    width=450,
    height=250,
    background_color='white',
    collocations=False,  # no overlapping words
    prefer_horizontal=1.0,  # horizontal words
    margin=12,  # space between words
    #contour_width=1,  # Add a slight contour around the words
    #contour_color='black',  # Set contour color to black
    max_font_size=50,  #  maximum font size
    min_font_size=13,
    relative_scaling=0.5,
    color_func=random_color_func  # random color functio
).generate(text)


buffer = io.BytesIO()
wordcloud.to_image().save(buffer, format='PNG')
buffer.seek(0)
image_base64 = base64.b64encode(buffer.getvalue()).decode()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
# App layout
app.layout = html.Div([
#     html.Div([
#     html.H4("Common places humanitarian migrants come from", style={'textAlign': 'left', 'color': 'purple'}),
#     html.Img(src=f'data:image/png;base64,{image_base64}', style={'width': '40%', 'height': '40%'})
# ]),
    html.Div([
        html.H4("Common places humanitarian migrants come from", style={'textAlign': 'left', 'color': 'purple', 'marginBottom': '12px', 'marginTop': '13px'}),
        html.Img(src=f'data:image/png;base64,{image_base64}', style={'width': '40%', 'height': 'auto', 'margin': '0 auto'})
    ]),
    
    #Text section
    html.Div([
        html.H6(
            'Identify key areas in Melbourne where your culture community thrives.',
            style={'textAlign': 'left', 'color': 'purple', 'fontSize': 16}
        ),
        html.H6(
            'Get a clear view of where you can find and connect with others from your community',
            style={'textAlign': 'left', 'color': 'purple', 'fontSize': 16}
        ),
        html.H6(
            'Select your country option to see where people from your community reside.',
            style={'textAlign': 'left', 'color': 'purple', 'fontSize': 16}
        )
    ], style={'marginBottom': '15px', 'marginTop': '9px', 'marginLeft': '9px'}),  # Added margin for spacing
    
    # html.Div([
    #     dcc.Dropdown(
    #         id='demo-dropdown',
    #         options=[{'label': country, 'value': country} for country in ['', 'Afghanistan', 'Iran', 'Myanmar', 'Iraq', 'Pakistan', 'Thailand',
    #             'Sri Lanka', 'Malaysia', 'India', 'Lebanon', 'Turkey', 'Cambodia',
    #             'Egypt', 'Papua New Guinea', 'Indonesia']],
    #         value='All'
    #     ),
    #     dcc.Graph(id='map', figure=map_fig)
    # ]),
    
    html.Div([
        dcc.Dropdown(
            id='demo-dropdown',
            options=[{'label': country, 'value': country} for country in ['', 'Afghanistan', 'Iran', 'Myanmar', 'Iraq', 'Pakistan', 'Thailand',
                    'Sri Lanka', 'Malaysia', 'India', 'Lebanon', 'Turkey', 'Cambodia',
                    'Egypt', 'Papua New Guinea', 'Indonesia']],
            value='All'
        )], style={'width': '40%', 'marginRight': '20px'}),  # Dropdown width and margin to separate from the graph
    
    
    # # Centering container for dropdown
    # html.Div([
    #     dcc.Dropdown(
    #         id='demo-dropdown',
    #         options=[{'label': country, 'value': country} for country in ['', 'Afghanistan', 'Iran', 'Myanmar', 'Iraq', 'Pakistan', 'Thailand',
    #                 'Sri Lanka', 'Malaysia', 'India', 'Lebanon', 'Turkey', 'Cambodia',
    #                 'Egypt', 'Papua New Guinea', 'Indonesia']],
    #         value='All'
    #     )
    # ], style={'width': '40%', 'margin': '0 auto'}),

    html.Div([
        dcc.Graph(id='map', figure=map_fig)]),
    # html.Div([
    #         dcc.Graph(id='map', figure=map_fig)])

    # html.Div(id='total-count', style={'textAlign': 'center', 'fontSize': 20, 'marginTop': '20px'}),
    # html.Div(id='city-count', style={'textAlign': 'center', 'fontSize': 20}),
    
    # html.Div([
    #     dcc.Graph(id='language-pie-chart')
    # ])
    # Modal for displaying information
    # dbc.Modal([
    #     dbc.ModalHeader("Details", close_button=True, style={'fontSize': 20, 'marginLeft': '20px'}),
    #     dbc.ModalBody([
    #         html.Div(id='total-count', style={'fontSize': 15, 'marginLeft': '20px'}),
    #         html.Div(id='city-count', style={'fontSize': 15, 'marginLeft': '20px'}),
    #         dcc.Graph(id='language-pie-chart', style={'width': '100%', 'height': '300px', 'margin': 'auto'})
    #     ]),
    #     dbc.ModalFooter(
    #         dbc.Button("x", id="close", className="ml-auto", style={'cursor': 'pointer', 'float': 'right', 'fontSize': '18px', 'color': '#666'})
    #     )
    # ], id="info-modal", is_open=False, style={
    #     'position': 'fixed',
    #     'bottom': '120px',
    #     'right': '20px',
    #     'width': '400px',
    #     'padding': '15px',
    #     'background': 'white',
    #     'border': '1px solid #ddd',
    #     'boxShadow': '0 0 10px rgba(0, 0, 0, 0.1)',
    #     'zIndex': '1000'
    # }),
    dbc.Modal([
        dbc.ModalHeader("Details"),
        dbc.ModalBody([
            html.Div(id='total-count', style={'fontSize': 15}),
            html.Div(id='city-count', style={'fontSize': 15}),
            dcc.Graph(id='language-pie-chart')
        ]),
        dbc.ModalFooter(
            dbc.Button("x", id="close", className="ml-auto")
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
            filtered_geo_data, geojson=geojson_data, locations=filtered_geo_data['name'],
            featureidkey="properties.name",
            color='Count', hover_name='Council Region',
            color_continuous_scale="Viridis",
            title=f'Regions with People from {selected_country}',
            mapbox_style="carto-positron", center={"lat": -37.8136, "lon": 144.9631}, zoom=8, opacity=0.8
        )

        if filtered_geo_data.empty:
            # Handle the case where there is no data to display
            return px.choropleth_mapbox(
                merged_geo_data, geojson=geojson_data, locations=merged_geo_data['name'],
                featureidkey="properties.name",
                color='Count', hover_name='Council Region',
                color_continuous_scale="Burg",
                title=f'No data available for {selected_country}',
                mapbox_style="carto-positron", center={"lat": -37.8136, "lon": 144.9631}, zoom=8, opacity=0.8
            )

    else:
        # Default to showing all regions
        map_fig = px.choropleth_mapbox(
            merged_geo_data, geojson=geojson_data, locations=merged_geo_data['name'],
            featureidkey="properties.name",
            color='Count', hover_name='Council Region',
            color_continuous_scale="Viridis",
            title='Regions with People from Selected Countries',
            mapbox_style="carto-positron", center={"lat": -37.8136, "lon": 144.9631}, zoom=8, opacity=0.8
        )

    map_fig.update_traces(
        marker_line_color='black',  # Darker border color
        marker_line_width=0.8  # Adjust border thickness
    )

    return map_fig

@app.callback(
    [Output('language-pie-chart', 'figure'),
     Output('total-count', 'children'),
     Output('city-count', 'children')],
    [Input('map', 'clickData'),
     Input('demo-dropdown', 'value')]
)
def update_pie_chart(clickData, selected_country):
    if clickData:
        selected_region = clickData['points'][0]['hovertext']
        top_languages = get_top_five_language(selected_region)

        filtered_data = csv_data[(csv_data['Country'] == selected_country) & (csv_data['Council Region'] == selected_region)]
        
        csv_data['Count'] = pd.to_numeric(csv_data['Count'], errors='coerce')

        total_count = csv_data[csv_data['Country'] == selected_country]['Count'].sum()
        city_count = filtered_data['Count'].sum()

        total_text = f"Total Count of people from {selected_country}: {int(total_count)}"
        city_text = f"Count of people from {selected_country} in {selected_region}: {int(city_count)}"

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
            }, total_text, city_text

        labels = [item['language'] for item in top_languages]
        values = [item['count'] for item in top_languages]

        return {
            "data": [{
                "type": "pie",
                "labels": labels,
                "values": values
            }],
            "layout": {
                "title": f"Top 5 Languages in {selected_region}"
            }
        }, total_text, city_text
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
        },  "Total Count: -", "City Count: -"

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

def get_top_five_language(region_name):
    # Load the CSV file into a DataFrame
    #file_path = 'merged_region_language.csv'
    
    try:
        # Read the CSV file
        #df = pd.read_csv(file_path)
        # Fetch data from the MySQL table
        query2 = "SELECT * FROM merged_region_language"
        df = pd.read_sql(query2, conn)
        
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
        return [{"language": language, "count": count} for language, count in top_five]

    except Exception as e:
        raise RuntimeError(f"Error processing data: {e}")

if __name__ == '__main__':
    app.run_server(debug=True)
