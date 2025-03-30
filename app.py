import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import json

#carregando as urls que foram armazenadas no .env
load_dotenv()

API_HOLIDAY = os.getenv('API_HOLIDAY')
API_OPEN_METEO = os.getenv('API_OPEN-METEO')

# 1. Quantos feriados há no Brasil em todo o ano de 2024?

def get_holidays():
    #setando variaveis da requisição
    year = 2024
    countryCode = 'BR'
    #requisição
    response = requests.get(f"{API_HOLIDAY}/{year}/{countryCode}")

    if response.status_code == 200:
        holidays = response.json()
        print(f"A quantidade de feriados no Brasil em {year} é de {len(holidays)}\n")
        return holidays
    else:
        print(f"Erro ao buscar feriados: {response.status_code}, {response.text}")
        return None

# 2. Qual mês de 2024 tem o maior número de feriados?
#Nesse caso preferi não trabalhar com api's contadoras para explorar mais a logica de programação.

def holiday_quantity():
    months = ['Janeiro','Fevereiro','Março','Abril','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    holiday_per_month = [0] * 12 

    #pegando a informacao dos feriados
    holidays = get_holidays()
    if holidays:
        for holiday in holidays:
            month = int(holiday["date"].split('-')[1])
            holiday_per_month[month - 1] +=1
            
        max_holidays = max(holiday_per_month)  
        month_index = holiday_per_month.index(max_holidays)
    print(f"\nO mês com mais feriados é {months[month_index]} com {max_holidays} feriados.\n")
    return months[month_index], max_holidays


# 3. Quantos feriados em 2024 caem em dias de semana (segunda a sexta-feira)?

def holiday_week():
    holidays_week = []
    days_week = ["Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira","Sexta-feira"]
    holidays = get_holidays()
    if holidays:
        for holiday in holidays:
            date_holiday = datetime.strptime(holiday['date'],"%Y-%m-%d")
            if date_holiday.weekday() < 5:
                holidays_week.append(holiday)
                print(f"O feriado {holiday["name"]} ocooreu no dia {days_week[date_holiday.weekday()]}")
            
    print(f"\nA quantidade total de feriados em dia de semana é de : {len(holidays_week)}\n")

#4. Qual foi a temperatura média em cada mês?   
def avarage_temp():
    params = {
    "latitude" : -22.9068,
    "longitude" : -43.1729,
    "start_date" : "2024-01-01",
    "end_date" : "2024-08-01",
    "hourly" : "temperature_2m"}
    url = API_OPEN_METEO
    response = requests.get(url, params=params)
    data = response.json()
    print(data)
    # Acessando e Estruturando os dados recebidos
    df = pd.DataFrame({
        'date': data['hourly']['time'],
        'temp_mean': data['hourly']['temperature_2m']
    })

    #ajusta os dados de data, mes e ano para assim conseguirmos gerar a media.
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month

    avg_temp = df.groupby(['month'])['temp_mean'].mean().reset_index()
    print(avg_temp)
    
#5.Qual foi o tempo predominante em cada mês nesse período?
#Para esse codigo foi necessarario tratar os dados desconhecidos para que fosse possivel ter um clima predominante

def get_weather_description(code):
    with open("descriptions.json", "r", encoding="utf-8") as file:
            weather_codes = json.load(file)
    code_str = str(code)
    if code_str in weather_codes:
        if "day" in weather_codes[code_str]:
            return weather_codes[code_str]["day"]["description"]
        else:
            return "Descrição do dia não encontrada"
    else:
        return "Desconhecido"
def weather_pred():
    params = {
        "latitude": -22.9064,
        "longitude": -43.1822,
        "start_date": "2024-01-01",
        "end_date": "2024-08-01",
        "daily": "weather_code"
    }
    url = API_OPEN_METEO
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        
        df = pd.DataFrame({
            'date': data['daily']['time'],
            'weather_code': data['daily']['weather_code']
        })

        #ajusta os dados de data, mes e ano para assim conseguirmos gerar a media.
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month

        weather_counts = df.groupby(['month', 'weather_code']).size().reset_index(name="count")
        most_common_weather = weather_counts.groupby("month")["count"].idxmax()
        most_common_weather_copy = weather_counts.iloc[most_common_weather].copy()
        
        most_common_weather_copy['weather_description'] = most_common_weather_copy['weather_code'].map(get_weather_description)
        print(most_common_weather_copy[['month', 'weather_description']].to_string(index=False))
    else:
        print(f"Erro ao buscar dados: {response.status_code}")


#6.Qual foi o tempo e a temperatura média em cada feriado de 01/01/2024 a 01/08/2024?

def weather_on_holidays():
    params = {
        "latitude": -22.9064,
        "longitude": -43.1822,
        "start_date": "2024-01-01",
        "end_date": "2024-08-01",
        "daily": ["weather_code", "temperature_2m_mean"]
    }
    url = API_OPEN_METEO
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        df_weather = pd.DataFrame({
            'date': data['daily']['time'],
            'weather_code': data['daily']['weather_code'],
            'temperature_2m_mean': data['daily']['temperature_2m_mean']
        })
        holidays = get_holidays()
        if holidays:
            holidays_dates = [holiday['date'] for holiday in holidays]

            df_weather['date'] = pd.to_datetime(df_weather['date'])
            holidays_dates = pd.to_datetime(holidays_dates)

            #filtra dados 
            df_holidays_weather = []
            for holiday_date in holidays_dates:
                holiday_weather = df_weather[df_weather['date'] == holiday_date]
                if not holiday_weather.empty:
                    df_holidays_weather.append(holiday_weather)
            df_holidays_weather = pd.concat(df_holidays_weather)
            print("Clima nos feriados de 2024:")
            print(df_holidays_weather[['date', 'temperature_2m_mean']])
            return df_holidays_weather
        else:
            print("Não foi possível obter os feriados.")
    else:
        print(f"Erro ao buscar o clima: {response.status_code}, {response.text}")

#7. Houve algum feriado "não aproveitável" em 2024? Se sim, qual(is)?
def no_enjoy_holidays():
    no_enjoy_holidays = []
    df_holidays_weather = weather_on_holidays()
    holidays = get_holidays()
    
    for _,row in df_holidays_weather.iterrows():
        if row['temperature_2m_mean'] < 20: 
            for holiday in holidays:
                if holiday['date'] == str(row['date']).split()[0]:
                    no_enjoy_holidays.append({
                        'date': row['date'].strftime('%Y-%m-%d'),
                        'temperature': row['temperature_2m_mean'],
                        'name': holiday['name']
                    })
        weather_description = get_weather_description(row['weather_code'])
        print(weather_description)

        if "sunny" not in weather_description.lower() or "mainly sunny" not in weather_description.lower():
            for  holiday in holidays:
                if holiday['date'] == str(row['date']).split()[0]:  
                        
                        no_enjoy_holidays.append({
                            'date': row['date'].strftime('%Y-%m-%d'),
                            'temperature': row['temperature_2m_mean'],
                            'weather_description': weather_description,
                            'name': holiday['name']
                        })
    df_no_enjoy_holidays = pd.DataFrame(no_enjoy_holidays)
    print("Feriados não aproveitados:")
    print(df_no_enjoy_holidays)
        

#8. Qual foi o feriado "mais aproveitável" de 2024?
def best_holiday():
    best_holiday = [] 
    bad_weather_conditions = ["light showers", "light rain", "rain", "foggy", "thunderstorm"]
    max_temp = 0
    df_holidays_weather = weather_on_holidays()
    holidays = get_holidays()

    for _, row in df_holidays_weather.iterrows():
        if row['temperature_2m_mean'] >= max_temp:
                
            max_temp = row['temperature_2m_mean']
            print('max_temp',max_temp)

            weather_description = get_weather_description(row['weather_code']) 
            print(weather_description)

            #agora vamos considerar que se tiver chuva nao sera uma boa escolha 
            if weather_description.lower() not in bad_weather_conditions:
                for holiday in holidays:
                    if pd.to_datetime(holiday['date']) == row['date']: 
                        best_holiday.append( {
                            'date': row['date'].strftime('%Y-%m-%d'),
                            'temperature': row['temperature_2m_mean'],
                            'weather_description': weather_description,
                            'name': holiday['name']})
    
    df_best_holiday = pd.DataFrame(best_holiday)
    print("Feriados não aproveitados:")
    print(df_best_holiday)

        


#get_holidays()
#holiday_quantity()
#holiday_week()
#avarage_temp()
#weather_pred()
#weather_on_holidays()
#no_enjoy_holidays()
best_holiday()

