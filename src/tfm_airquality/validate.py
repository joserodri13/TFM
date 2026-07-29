from dataclasses import dataclass, field
import pandas as pd
from tfm_airquality import config

@dataclass
class Check:
    """Resultado de una comprobación individual del data contract."""
    nombre: str
    ok: bool
    detalle: str = ""
    bloqueante: bool = True

    def __str__(self):
        if self.ok:
            marca = "OK"
        elif self.bloqueante:
            marca = "FALLO"
        else:
            marca = "AVISO"
        return f"[{marca:5s}] {self.nombre}: {self.detalle}"


@dataclass
class ValidationReport:
    """Conjunto de comprobaciones ejecutadas sobre una tabla."""
    checks: list = field(default_factory=list)

    @property
    def ok(self):
        """True si no ha fallado ninguna comprobación bloqueante."""
        return all(c.ok for c in self.checks if c.bloqueante)

    @property
    def fallos(self):
        return [c for c in self.checks if not c.ok and c.bloqueante]

    @property
    def avisos(self):
        return [c for c in self.checks if not c.ok and not c.bloqueante]

    def __str__(self):
        cabecera = "DATA CONTRACT: " + ("SUPERADO" if self.ok else "RECHAZADO")
        lineas = [cabecera, "-" * len(cabecera)]
        lineas += [str(c) for c in self.checks]
        return "\n".join(lineas)

    def raise_if_failed(self):
        """Detiene el pipeline si alguna comprobación bloqueante ha fallado."""
        if not self.ok:
            motivos = "\n".join(f"  - {c.nombre}: {c.detalle}" for c in self.fallos)
            raise ValueError(f"El fichero no cumple el data contract:\n{motivos}")


# ---------------------------------------------------------------------------
# Comprobaciones bloqueantes
# ---------------------------------------------------------------------------

def check_columns(df):
    """Comprueba que están las 13 columnas esperadas y ninguna más."""
    faltan = set(config.EXPECTED_COLUMNS) - set(df.columns)
    sobran = set(df.columns) - set(config.EXPECTED_COLUMNS)

    if faltan or sobran:
        problemas = []
        if faltan:
            problemas.append(f"faltan {sorted(faltan)}")
        if sobran:
            problemas.append(f"sobran {sorted(sobran)}")
        return Check("columnas", False, "; ".join(problemas))

    return Check("columnas", True, f"{len(df.columns)} columnas correctas")


def check_types(df):
    """Todas las columnas deben ser numéricas."""
    no_numericas = [
        c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])
    ]
    if no_numericas:
        return Check("tipos", False, f"no son numéricas: {no_numericas}")
    return Check("tipos", True, "todas las columnas son numéricas")


def check_index(df):
    """El índice debe ser temporal, ordenado, único y sin saltos horarios."""
    if not isinstance(df.index, pd.DatetimeIndex):
        return Check("índice", False, "el índice no es de tipo fecha")

    if not df.index.is_monotonic_increasing:
        return Check("índice", False, "el índice no está ordenado")

    if df.index.has_duplicates:
        n = int(df.index.duplicated().sum())
        return Check("índice", False, f"{n} sellos temporales duplicados")

    saltos = df.index.to_series().diff().dropna()
    anomalos = saltos[saltos != pd.Timedelta(hours=1)]
    if len(anomalos) > 0:
        return Check(
            "índice", False,
            f"{len(anomalos)} saltos distintos de 1 hora (máximo {anomalos.max()})"
        )

    return Check(
        "índice", True,
        f"{len(df)} horas consecutivas, "
        f"{df.index.min():%d/%m/%Y %H:%M} a {df.index.max():%d/%m/%Y %H:%M}"
    )


def check_ranges(df):
    """
    Los valores deben caer dentro de cotas de sentido común.

    Es la única comprobación que detecta un error de lectura que no altera ni
    la forma, ni el tipo, ni el índice de la tabla.

    El marcador -200 se excluye del examen: no es una medición.
    """
    problemas = []

    for col, (minimo, maximo) in config.PLAUSIBLE_RANGES.items():
        if col not in df.columns:
            continue
        serie = df[col]
        serie = serie[serie != config.MISSING_SENTINEL].dropna()
        fuera = serie[(serie < minimo) | (serie > maximo)]
        if len(fuera) > 0:
            problemas.append(
                f"{col}: {len(fuera)} valores fuera de [{minimo}, {maximo}] "
                f"(min {fuera.min():.1f}, max {fuera.max():.1f})"
            )

    if problemas:
        return Check("rangos", False, "; ".join(problemas))
    return Check("rangos", True, "todos los valores son plausibles")


# ---------------------------------------------------------------------------
# Comprobaciones informativas
# ---------------------------------------------------------------------------

def check_row_count(df):
    """Informa si el número de filas difiere del esperado."""
    if len(df) != config.EXPECTED_ROWS:
        return Check(
            "nº de filas", False,
            f"{len(df)} filas, se esperaban {config.EXPECTED_ROWS}",
            bloqueante=False,
        )
    return Check("nº de filas", True, f"{len(df)} filas", bloqueante=False)


def check_missing_sentinel(df):
    """
    Informa de cuántos -200 hay y en qué columnas.

    Nunca falla: la abundancia de ausentes es una característica del dataset,
    no un defecto del fichero. El recuento es documental.
    """
    por_columna = (df == config.MISSING_SENTINEL).sum()
    total = int(por_columna.sum())
    celdas = df.size

    peores = por_columna.sort_values(ascending=False).head(3)
    resumen = ", ".join(
        f"{col} {100 * n / len(df):.1f}%" for col, n in peores.items() if n > 0
    )

    return Check(
        "marcador -200", True,
        f"{total} celdas ({100 * total / celdas:.1f}% del total). Mayores: {resumen}",
        bloqueante=False,
    )


def check_target_coverage(df):
    """Informa de si el objetivo tiene cobertura suficiente para modelar."""
    if config.TARGET not in df.columns:
        return Check("cobertura objetivo", False, f"falta {config.TARGET}", bloqueante=False)

    serie = df[config.TARGET]
    observados = int(((serie != config.MISSING_SENTINEL) & serie.notna()).sum())
    pct = 100 * observados / len(df)

    if pct < config.MIN_TARGET_COVERAGE:
        return Check(
            "cobertura objetivo", False,
            f"solo {pct:.1f}% de {config.TARGET} observado (mínimo {config.MIN_TARGET_COVERAGE}%)",
            bloqueante=False,
        )
    return Check(
        "cobertura objetivo", True,
        f"{observados} horas observadas de {config.TARGET} ({pct:.1f}%)",
        bloqueante=False,
    )


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def validate(df):
    """
    Ejecuta el contrato completo y devuelve el informe.

    Ninguna comprobación lanza excepciones: todas devuelven su resultado, de
    modo que un solo diagnóstico muestra todos los problemas a la vez en lugar
    de obligar a corregirlos de uno en uno.
    """
    return ValidationReport(checks=[
        check_columns(df),
        check_types(df),
        check_index(df),
        check_ranges(df),
        check_row_count(df),
        check_missing_sentinel(df),
        check_target_coverage(df),
    ])