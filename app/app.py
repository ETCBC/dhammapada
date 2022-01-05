import types
from tf.advanced.app import App


MODIFIERS = "quote uncertain clarity trans extrastanza".strip().split()


def fmt_layoutOrig(app, n, **kwargs):
    return app._wrapHtml(n, None)


def fmt_layoutPali(app, n, **kwargs):
    return app._wrapHtml(n, False)


def fmt_layoutLatin(app, n, **kwargs):
    return app._wrapHtml(n, True)


class TfApp(App):
    def __init__(app, *args, **kwargs):
        app.fmt_layoutOrig = types.MethodType(fmt_layoutOrig, app)
        app.fmt_layoutPali = types.MethodType(fmt_layoutPali, app)
        app.fmt_layoutLatin = types.MethodType(fmt_layoutLatin, app)
        super().__init__(*args, **kwargs)

    def _wrapHtml(app, n, kind):
        api = app.api
        F = api.F
        Fs = api.Fs
        trans = F.trans.v(n)
        before = (
            (F.latinpre.v(n) if trans else F.palipre.v(n))
            if kind is None
            else F.latinpre.v(n)
            if kind
            else F.palipre.v(n)
        ) or ""
        after = (
            (F.latinpost.v(n) if trans else F.palipost.v(n))
            if kind is None
            else F.latinpost.v(n)
            if kind
            else F.palipost.v(n)
        ) or ""
        material = (
            (F.latin.v(n) if trans else F.pali.v(n))
            if kind is None
            else F.latin.v(n)
            if kind
            else F.pali.v(n)
        ) or ""
        clses = " ".join(f"{cf}{Fs(cf).v(n)}" for cf in MODIFIERS if Fs(cf).v(n))
        return (
            f'<span class="{clses}">{before}{material}{after}</span>'
            if clses
            else f"{before}{material}{after}"
        )
