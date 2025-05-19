# !pip install pandas flask matplotlib openpyxl

#import os
from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
import base64
import io
#import os と importbase64,ioたぶんどちらかが必要ってことだと思われる。cje1資料のなかでやっていたテキストファイルcjeinstallを参照したところ。

#os.chdir("")
#osをつかいたいフォルダ、すなわちここにはhtmlやexcelファイルが入っているフォルダのパス。cje1installのなかの装備

app = Flask(__name__)
#cje1gw.run_with(app)#ここはわからん　cje1gwはcje1installのなかにあるもの。cje1installのなかでやっていたこと。

# Excel 読み込み
df = pd.read_excel("date/grades_2024.xlsx", sheet_name="Table 1")

@app.route("/report.html")
def report():
    return render_template("report.html")

@app.route('/keyword', methods=['POST'])
def keyword():
    search_type = request.form['search_type']
    keyword = request.form['word'].strip()

    # 科目名 or 科目番号で検索
    if search_type == "title":
        matches = df[df["科⽬名称"].str.contains(keyword, na=False)]
    else:
        matches = df[df["科⽬番号"].astype(str).str.contains(keyword, na=False)]

    results = matches.to_dict(orient='records')
    count = len(results)

    return render_template('result.html', results=results, count=count)

@app.route('/graph/<subject_id>')
def show_graph(subject_id):
    match = df[df["科⽬番号"].astype(str) == subject_id]
    if match.empty:
        return "科目が見つかりませんでした"

    row = match.iloc[0]
    grades = ["A_plus_members", "A_members", "B_members", "C_members", "D_members"]
    labels = ["A+", "A", "B", "C", "D"]
    counts = [row[g] for g in grades]

    # グラフを画像として返す
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90, counterclock=False)
    ax.set_title(f"{row['科⽬名称']} の成績分布")
    ax.axis('equal')

    # グラフをBase64に変換
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    return render_template('graph.html', subject_name=row['科⽬名称'], plot_url=plot_url)

@app.route('/back', methods=['POST'])
def back():
    return render_template('report.html')

if __name__ == '__main__':
    app.run(debug=True)
