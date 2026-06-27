import json

from django.shortcuts import render

from .forms import TickerForm
from .services.finance import AnalysisError, analyze, resolve_ticker


def index(request):
    """単一ページのビュー。

    GET ?query=... で財務データを取得して表示する。
    （Streamlit版の「入力 → ボタン → 表示」を1画面で再現）
    """
    form = TickerForm(request.GET or None)
    context = {"form": form, "result": None, "error": None, "resolved": None}

    # クエリが送られている場合のみ処理
    if request.GET and form.is_valid():
        user_input = form.cleaned_data["query"]
        context["resolved"] = resolve_ticker(user_input)
        try:
            result = analyze(user_input)
            context["result"] = result
            # Chart.js 用にトレンドデータを JSON 文字列化して渡す
            context["trend_json"] = json.dumps(result["trend"], ensure_ascii=False)
        except AnalysisError as exc:
            context["error"] = str(exc)

    return render(request, "analyzer/index.html", context)
