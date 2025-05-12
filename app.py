from flask import Flask, render_template # flaskモジュールの中のFlaskクラスをインポート

# -- インスタンス生成 --
app = Flask(__name__)  # Flaskクラスを使ってアプリのインスタンスを作成。引数には__name__を指定

# -- ルーティング --
@app.route("/")         # ルートURL（http://〜/）にアクセスがあった時の処理を定義
def hello_flask():      # 関数hello_flaskを定義
    return '<h1>HelloFlask!</h1>'  # ブラウザに表示するHTML文字列を返す


# 動的ルーティング：URLの一部を変数animalとして受け取る
@app.route("/<animal>")
def animal_info(animal):
    """
    animal（動物の名前）を受け取り、その特徴を返す関数
    """

    # 動物の名前に応じて特徴を返す辞書を作成（簡単な例）
    features = {
        "ねこ": "静かで気まぐれな性格です。",
        "いぬ": "忠実で人懐っこい動物です。",
        "うさぎ": "耳が長くてぴょんぴょん跳ねます。",
        "とり": "空を飛ぶことができます。",
    }

    # 指定された動物が辞書にあれば、その特徴を返す
    if animal in features:
        #return f"<h1>{animal}の特徴：</h1><p>{features[animal]}</p>"
        return  render_template("animal.html", animal=animal, features=features[animal])
    else:
        return f"<h1>{animal}についての情報は登録されていません。</h1>"
        # 辞書にない動物名が来た場合の処理
        #return f"<h1>{animal}についての情報は登録されていません。</h1>"