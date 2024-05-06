import base64
import io

from flask import Response

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


def _fig2png(fig: Figure) -> bytes:
    png = io.BytesIO()
    FigureCanvas(fig).print_png(png)
    return png.getvalue()


def fig2png_Response(fig: Figure) -> Response:
    return Response(_fig2png(fig), mimetype="image/png")


def fig2png_base64(fig: Figure) -> str:
    return "data:image/png;base64," + base64.b64encode(_fig2png(fig)).decode()


def parse_form(form: dict[str, str]) -> list:
    result = [0] * len(form)
    for k, v in form.items():
        index = int(k.split("[")[1].removesuffix("]"))
        result[index] = int(v)
    return result
