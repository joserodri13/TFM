import matplotlib.pyplot as plt
import pandas as pd

from tfm_airquality import config

def correlacion_por_horizonte(df, variables=None, horizontes=(0, 1, 6, 24, 48)):
    """
    Correlación de cada variable con el objetivo desplazado a cada horizonte.

    La correlación contemporánea no mide capacidad predictiva: lo relevante es
    la relación entre el valor de ahora y el objetivo de dentro de h horas.
    """
    if variables is None:
        variables = [c for c in df.columns
                     if c in config.SENSOR_COLUMNS + config.MET_COLUMNS
                     or c in config.GT_COLUMNS]
        variables = [c for c in variables if c != config.TARGET]

    y = df[config.TARGET]

    filas = []
    for col in variables:
        fila = {'variable': col}
        for h in horizontes:
            fila[f'h+{h}' if h else 'lag0'] = df[col].corr(y.shift(-h))
        filas.append(fila)

    return pd.DataFrame(filas).set_index('variable').round(3)

def plot_perfiles_temporales(df, columna=None, figsize=(12, 4)):
    """Perfil medio del objetivo por hora del día y por día de la semana."""
    columna = columna or config.TARGET

    horario = df.groupby(df.index.hour)[columna].mean()
    semanal = df.groupby(df.index.dayofweek)[columna].mean()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    ax1.plot(horario.index, horario.values, marker='o')
    ax1.set_xlabel('hora del día')
    ax1.set_ylabel(f'{columna} medio (µg/m³)')
    ax1.set_xticks(range(0, 24, 3))
    ax1.grid(alpha=0.3)

    dias = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    ax2.bar(dias, semanal.values)
    ax2.set_xlabel('día de la semana')
    ax2.grid(alpha=0.3, axis='y')

    # Eje Y común: sin esto, dos escalas distintas harían parecer que la
    # variación semanal es tan grande como la diaria, y no lo es.
    minimo = min(horario.min(), semanal.min()) * 0.9
    maximo = max(horario.max(), semanal.max()) * 1.05
    ax1.set_ylim(minimo, maximo)
    ax2.set_ylim(minimo, maximo)

    fig.tight_layout()
    return fig

def plot_matriz_correlacion(matriz, figsize=(9, 7), titulo='Matriz de correlación'):
    """Mapa de calor de una matriz de correlación."""
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(matriz, cmap='RdBu_r', vmin=-1, vmax=1)

    ax.set_xticks(range(len(matriz.columns)), matriz.columns, rotation=90)
    ax.set_yticks(range(len(matriz.index)), matriz.index)
    ax.set_title(titulo)

    # Los valores dentro de las celdas: un mapa de calor sin cifras obliga a
    # estimar a ojo.
    for i in range(len(matriz.index)):
        for j in range(len(matriz.columns)):
            ax.text(j, i, f'{matriz.iloc[i, j]:.2f}', ha='center', va='center',
                    fontsize=7)

    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    return fig

def plot_autocorrelacion(df, columna=None, max_lag=192, figsize=(12, 4)):
    """Autocorrelación del objetivo, con los retardos relevantes destacados."""
    columna = columna or config.TARGET
    serie = df[columna]

    lags = range(1, max_lag + 1)
    valores = [serie.autocorr(lag) for lag in lags]

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(lags, valores, linewidth=1)

    # Los tres retardos con justificación propia: horario, diario y semanal.
    for lag, etiqueta in [(1, '1 h'), (24, '24 h'), (168, '168 h')]:
        if lag <= max_lag:
            ax.axvline(lag, color='tab:red', linestyle='--', alpha=0.5)
            ax.annotate(f'{etiqueta}\n{serie.autocorr(lag):.2f}',
                        xy=(lag, serie.autocorr(lag)),
                        xytext=(lag + 4, serie.autocorr(lag) + 0.05),
                        fontsize=8, color='tab:red')

    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_xlabel('retardo (horas)')
    ax.set_ylabel('autocorrelación')
    ax.set_xticks(range(0, max_lag + 1, 24))
    ax.grid(alpha=0.3)

    fig.tight_layout()
    return fig

def plot_deriva_sensores(df, columna=None, figsize=(11, 5)):
    """
    Evolución mensual del cociente entre concentración de referencia y señal
    de cada sensor. Si el cociente se desplaza, la relación entre sensor y
    concentración ha cambiado.
    """
    columna = columna or config.TARGET
    mes = df.index.to_period('M')

    fig, ax = plt.subplots(figsize=figsize)

    for s in config.SENSOR_COLUMNS:
        ratio = (df.groupby(mes)[columna].mean() / df.groupby(mes)[s].mean()) * 1000
        ax.plot(ratio.index.to_timestamp(), ratio.values, marker='o',
                label=s, linewidth=1.5)

    ax.set_ylabel(f'{columna} medio / señal media  (×1000)')
    ax.set_xlabel('mes')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    fig.tight_layout()
    return fig

def plot_simpson(df, sensor='PT08.S4(NO2)', columna=None, figsize=(8, 6)):
    """
    Dispersión sensor-objetivo coloreada por mes.

    Muestra por qué la correlación global de PT08.S4 es baja pese a que sus
    correlaciones mensuales son altas: la relación existe dentro de cada mes,
    pero el nivel base se desplaza entre meses.
    """
    columna = columna or config.TARGET
    d = df[[sensor, columna]].dropna()
    mes = d.index.to_period('M')

    fig, ax = plt.subplots(figsize=figsize)
    sc = ax.scatter(d[sensor], d[columna], c=mes.astype('int64'),
                    cmap='viridis', s=4, alpha=0.5)

    ax.set_xlabel(f'{sensor} (señal)')
    ax.set_ylabel(f'{columna} (µg/m³)')

    cb = fig.colorbar(sc, ax=ax)
    cb.set_label('mes (de marzo 2004 a abril 2005)')

    fig.tight_layout()
    return fig

def plot_baselines(resultados, figsize=(11, 5)):
    """Curva de error de cada baseline según el horizonte de predicción."""
    fig, ax = plt.subplots(figsize=figsize)

    for nombre, tabla in resultados.items():
        ax.plot(tabla.index, tabla['MAE'], marker='.', label=nombre)

    ax.set_xlabel('horizonte (horas)')
    ax.set_ylabel('MAE (µg/m³)')
    ax.set_xticks(range(0, 49, 6))
    ax.legend()
    ax.grid(alpha=0.3)

    fig.tight_layout()
    return fig

def guardar_figura(fig, nombre):
    """Guarda una figura en reports/figuras/, creando la carpeta si hace falta."""
    destino = config.RAIZ / 'reports' / 'figuras'
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / f'{nombre}.png'
    fig.savefig(ruta, dpi=150, bbox_inches='tight')
    return ruta