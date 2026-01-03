import os
import time
import random
import logging
from datetime import datetime
import mysql.connector

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'mysql'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'database': os.getenv('MYSQL_DATABASE', 'weather_station'),
    'user': os.getenv('MYSQL_USER', 'user'),
    'password': os.getenv('MYSQL_PASSWORD', 'user12345')
}

# Города для генерации станций
CITIES = ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 
          'Казань', 'Нижний Новгород', 'Красноярск', 'Владивосток']

# Улицы для генерации адресов
STREETS = [
    'ул. Ленина', 'ул. Пушкина', 'ул. Гагарина', 'пр. Мира', 
    'ул. Советская', 'ул. Центральная', 'ул. Школьная', 'ул. Садовая'
]

# Типы датчиков
SENSOR_TYPES = {
    'temperature': {'name': 'temperature', 'units': '°C', 'base': 15, 'min': -30, 'max': 40, 'variation': 3},
    'humidity': {'name': 'humidity', 'units': '%', 'base': 65, 'min': 20, 'max': 100, 'variation': 8},
    'pressure': {'name': 'pressure', 'units': 'hPa', 'base': 1013, 'min': 950, 'max': 1050, 'variation': 15},
    'wind_speed': {'name': 'wind_speed', 'units': 'м/с', 'base': 4, 'min': 0, 'max': 20, 'variation': 2},
    'noise_level': {'name': 'noise_level', 'units': 'дБ', 'base': 55, 'min': 30, 'max': 90, 'variation': 8}
}

# Климатические поправки
CLIMATE_ZONES = {
    'Москва': {'temp_mod': 0, 'hum_mod': 0, 'pressure_mod': 0, 'noise_mod': 0},
    'Санкт-Петербург': {'temp_mod': -2, 'hum_mod': 10, 'pressure_mod': -5, 'noise_mod': -5},
    'Новосибирск': {'temp_mod': -5, 'hum_mod': -5, 'pressure_mod': -10, 'noise_mod': -8},
    'Екатеринбург': {'temp_mod': -3, 'hum_mod': -3, 'pressure_mod': -8, 'noise_mod': -3},
    'Казань': {'temp_mod': -1, 'hum_mod': 0, 'pressure_mod': -3, 'noise_mod': 0},
    'Нижний Новгород': {'temp_mod': -1, 'hum_mod': 2, 'pressure_mod': -4, 'noise_mod': -2},
    'Красноярск': {'temp_mod': -6, 'hum_mod': -8, 'pressure_mod': -12, 'noise_mod': -5},
    'Владивосток': {'temp_mod': 1, 'hum_mod': 15, 'pressure_mod': 2, 'noise_mod': 5}
}

def generate_address(city):
    street = random.choice(STREETS)
    house = random.randint(1, 100)
    address = f"{city}, {street}, д. {house}"
    
    return address.strip()

def generate_sensor_code(city, sensor_type, sensor_num):
    """Генерация кода датчика SCTXXXXXXX"""
    city_first = city[0].upper()
    type_first = sensor_type[0].upper()
    number = str(sensor_num).zfill(7)
    
    return f"S{city_first}{type_first}{number}"

def check_table_count(table_name):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Ошибка при проверке таблицы {table_name}: {e}")
        return 0

def init_stations():
    """Инициализирует таблицу Station"""
    count = check_table_count('Station')
    if count == 0:
        logger.info("Заполнение таблицы Station...")
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            stations = []
            for city in CITIES:
                num_stations = random.randint(1, 2)
                for i in range(num_stations):
                    address = generate_address(city)
                    stations.append((address,))
            
            cursor.executemany("INSERT INTO Station (address) VALUES (%s)", stations)
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Добавлено {len(stations)} станций")
            return True
        except Exception as e:
            logger.error(f"Ошибка заполнения Station: {e}")
            return False
    else:
        logger.info(f"Таблица Station уже содержит {count} записей")
        return True

def init_sensor_types():
    """Инициализирует таблицу Sensor_type"""
    count = check_table_count('Sensor_type')
    if count == 0:
        logger.info("Заполнение таблицы Sensor_type...")
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            sensor_type_data = [(st['name'], st['units']) for st in SENSOR_TYPES.values()]
            cursor.executemany("INSERT INTO Sensor_type (type, units) VALUES (%s, %s)", sensor_type_data)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Добавлено {len(sensor_type_data)} типов датчиков")
            return True
        except Exception as e:
            logger.error(f"Ошибка заполнения Sensor_type: {e}")
            return False
    else:
        logger.info(f"Таблица Sensor_type уже содержит {count} записей")
        return True

def init_sensors():
    """Инициализирует таблицу Sensor"""
    count = check_table_count('Sensor')
    if count == 0:
        logger.info("Заполнение таблицы Sensor...")
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Получаем ID станций
            cursor.execute("SELECT id, address FROM Station")
            stations_data = cursor.fetchall()
            
            station_city_map = {}
            for station_id, address in stations_data:
                for city in CITIES:
                    if city in address:
                        station_city_map[station_id] = city
                        break
            
            # Получаем ID типов датчиков
            cursor.execute("SELECT id, type FROM Sensor_type")
            type_map = {row[1]: row[0] for row in cursor.fetchall()}
            
            # Создаем датчики
            sensors_data = []
            sensor_counter = 1
            
            for station_id, city in station_city_map.items():
                for sensor_type_name in SENSOR_TYPES.keys():
                    num_sensors = random.randint(1, 2)
                    for i in range(num_sensors):
                        sensor_code = generate_sensor_code(city, sensor_type_name, sensor_counter)
                        sensors_data.append((sensor_code, type_map[sensor_type_name], station_id))
                        sensor_counter += 1
            
            cursor.executemany("INSERT INTO Sensor (sensor_code, type_id, station_id) VALUES (%s, %s, %s)", sensors_data)
            
            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"Добавлено {len(sensors_data)} датчиков")
            return True
        except Exception as e:
            logger.error(f"Ошибка заполнения Sensor: {e}")
            return False
    else:
        logger.info(f"Таблица Sensor уже содержит {count} записей")
        return True

def init_database():
    logger.info("Проверка справочных таблиц...")
    
    success = True
    
    if not init_stations():
        success = False
    
    if not init_sensor_types():
        success = False
    
    if not init_sensors():
        success = False
    
    return success

def get_sensors_with_info():
    """Получает список датчиков"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT s.sensor_code, st.type as sensor_type, sta.address
            FROM Sensor s
            JOIN Sensor_type st ON s.type_id = st.id
            JOIN Station sta ON s.station_id = sta.id
        """)
        
        sensors = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return sensors
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка датчиков: {e}")
        return []

def get_city_from_address(address):
    """Извлекает город из адреса"""
    for city in CITIES:
        if city in address:
            return city
    return "Москва"

def generate_sensor_value(sensor_info):
    """Генерирует значение датчика"""
    sensor_type = sensor_info['sensor_type']
    address = sensor_info['address']
    
    sensor_config = SENSOR_TYPES.get(sensor_type)
    if not sensor_config:
        return 0
    
    city = get_city_from_address(address)
    climate_mod = CLIMATE_ZONES.get(city, CLIMATE_ZONES['Москва'])
    
    base_value = sensor_config['base']
    
    if sensor_type == 'temperature':
        base_value += climate_mod['temp_mod']
    elif sensor_type == 'humidity':
        base_value += climate_mod['hum_mod']
        base_value = min(base_value, 95)
    elif sensor_type == 'pressure':
        base_value += climate_mod['pressure_mod']
    elif sensor_type == 'noise_level':
        base_value += climate_mod['noise_mod']
    
    deviation = random.uniform(-sensor_config['variation'], sensor_config['variation'])
    
    current_hour = datetime.now().hour
    
    if sensor_type == 'temperature':
        if 12 <= current_hour <= 16:
            deviation += 3
        elif 0 <= current_hour <= 4:
            deviation -= 4
    elif sensor_type == 'humidity':
        if 0 <= current_hour <= 8:
            deviation += 10
        elif 12 <= current_hour <= 16:
            deviation -= 8
    elif sensor_type == 'noise_level':
        if 8 <= current_hour <= 20:
            deviation += 15
        elif 22 <= current_hour <= 6:
            deviation -= 20
    
    value = base_value + deviation
    value = max(sensor_config['min'], min(sensor_config['max'], value))
    
    if sensor_type in ['temperature', 'wind_speed']:
        value = round(value, 1)
    elif sensor_type in ['humidity', 'noise_level', 'pressure']:
        value = round(value)
    
    return value

def generate_measurements():
    """Генерирует измерения"""
    try:
        sensors = get_sensors_with_info()
        if not sensors:
            logger.warning("Нет датчиков для генерации данных")
            return 0
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        for sensor in sensors:
            value = generate_sensor_value(sensor)
            cursor.execute("INSERT INTO Measurement (sensor_code, value) VALUES (%s, %s)", (sensor['sensor_code'], value))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return len(sensors)
        
    except Exception as e:
        logger.error(f"Ошибка генерации измерений: {e}")
        return 0

def main():
    """Основная функция"""
    logger.info("Запуск генератора погодных данных")
    
    # Инициализируем справочные таблицы
    if not init_database():
        logger.error("Ошибка инициализации справочных таблиц")
        return
    
    interval = float(os.getenv('GENERATION_INTERVAL', '1.0'))
    max_cycles = 20
    
    logger.info(f"Начало генерации измерений (интервал: {interval}с, циклов: {max_cycles})")
    
    for cycle in range(1, max_cycles + 1):
        try:
            count = generate_measurements()
            if count > 0:
                logger.info(f"Сгенерировано измерений: {count}")
            
            time.sleep(interval)
            
        except KeyboardInterrupt:
            logger.info("Остановлено пользователем")
            break
        except Exception as e:
            logger.error(f"Ошибка цикла: {e}")
            time.sleep(5)
    
    logger.info("Генерация завершена")

if __name__ == "__main__":
    main()