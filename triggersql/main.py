import pandas as pd

def convert_datetime_format(input_file, output_file):
    # Read the Excel file
    df = pd.read_excel(input_file)
    
    # Función para convertir diferentes formatos de hora
    def parse_time(time_str):
        try:
            # Intentar convertir a hora en formato HH:MM
            time_formats = [
                '%d/%m/%Y %I:%M:%S %p',  # Formato con fecha
                '%H:%M:%S',              # Formato 24 horas
                '%I:%M:%S %p'            # Formato 12 horas
            ]
            
            for fmt in time_formats:
                try:
                    # Convertir a datetime y luego calcular minutos totales
                    tiempo = pd.to_datetime(time_str, format=fmt)
                    total_minutos = tiempo.hour * 60 + tiempo.minute
                    
                    # Calcular horas y minutos
                    horas = total_minutos // 60
                    minutos = total_minutos % 60
                    
                    return f"{horas:02d}:{minutos:02d}"
                except ValueError:
                    continue
            
            return time_str  # Si no se puede convertir, devuelve el valor original
        except Exception as e:
            print(f"Error al convertir {time_str}: {e}")
            return time_str
    
    # Aplicar conversión a la columna
    df['arrival_dead_time'] = df['arrival_dead_time'].apply(parse_time)
    
    # Guardar archivo convertido
    df.to_excel(output_file, index=False)
    
    print(f"Archivo convertido guardado como {output_file}")

# Example usage
input_file = 'ingreformat.xlsx'
output_file = 'output.xlsx'
convert_datetime_format(input_file, output_file)