from bs4 import BeautifulSoup
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import altair as alt
import streamlit as st

def get_df_ec():
    url_ec = "https://scraping.official.ec/"
    res = requests.get(url_ec)
    soup = BeautifulSoup(res.text, 'html.parser')
    item_list = soup.find('ul', {'id':'itemList'})
    items = item_list.find_all('li')

    data_ec = []
    for item in items:
        datam_ec = {}
        datam_ec['title'] = item.find('p', {'class':'items-grid_itemTitleText_8125e001'}).text
        price = item.find('p', {'class':'items-grid_price_8125e001'}).text
        datam_ec['price'] = price.replace('¥', '').replace(',', '')
        datam_ec['link'] = item.find('a')['href']
        is_stock = item.find('p', {'class':'items-grid_soldOut_8125e001'}) == None
        datam_ec['is_stock'] = '在庫あり' if is_stock == True else '在庫なし'
        data_ec.append(datam_ec)
    df_ec = pd.DataFrame(data_ec)
    return df_ec

def get_worksheet():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    credentials = Credentials.from_service_account_info(
        # secrets.toml
        st.secrets["GCP_SERVICE_ACCOUNT"],
        scopes=scopes
    )

    gc = gspread.authorize(credentials)

    # secrets.toml
    SP_SHEET_KEY = st.secrets.SP_SHEET_KEY.key
    sh = gc.open_by_key(SP_SHEET_KEY)
    SP_SHEET = 'db'
    worksheet = sh.worksheet(SP_SHEET)
    return worksheet

def get_chart():
    worksheet = get_worksheet()

    data = worksheet.get_all_values()
    df_udemy = pd.DataFrame(data[1:], columns=data[0])
    df_udemy = df_udemy.astype({
        'n_subscriber': int,
        'n_review': int    
    })
    ymin1 = df_udemy['n_subscriber'].min() - 10
    ymax1 = df_udemy['n_subscriber'].max() + 10
    ymin2 = df_udemy['n_review'].min() - 10
    ymax2 = df_udemy['n_review'].max() + 10

    base = alt.Chart(df_udemy).encode(
        alt.X('date:T', axis=alt.Axis(title=None))
    )
    line1 = base.mark_line(opacity=0.3, color='#57A44C').encode(
        alt.Y('n_subscriber',
            axis=alt.Axis(title='受講生数', titleColor='#57A44C'),
            scale=alt.Scale(domain=[ymin1, ymax1])
            )
    )
    line2 = base.mark_line(stroke='#5276A7', interpolate='monotone').encode(
        alt.Y('n_review',
            axis=alt.Axis(title='レビュー数', titleColor='#5276A7'),
            scale=alt.Scale(domain=[ymin2, ymax2])
            )
    )
    chart = alt.layer(line1, line2).resolve_scale(
        y = 'independent'
    )
    return chart

st.title('Scraping')
st.write(get_df_ec())

st.title('Spreadsheet')
chart = get_chart()
st.altair_chart(chart, use_container_width=True)


