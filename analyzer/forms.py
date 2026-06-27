from django import forms


class TickerForm(forms.Form):
    """企業名・株式コード・ティッカーの入力フォーム。"""

    query = forms.CharField(
        label="企業名・株式コード・ティッカー",
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "例：Apple、AAPL、トヨタ、7203",
                "class": "ticker-input",
                "autofocus": "autofocus",
            }
        ),
        error_messages={"required": "企業名・株式コード・ティッカーを入力してください。"},
    )
