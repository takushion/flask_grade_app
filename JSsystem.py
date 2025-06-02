from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)
# excel 読み込み
year = "average"  # デフォルトのシート名
df = pd.read_excel("date/grades_full.xlsx", sheet_name=year)

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
    year = request.args.get('year', 'average') 
    df = pd.read_excel("date/grades_full.xlsx", sheet_name=year)
    match = df[df["科⽬番号"].astype(str) == subject_id]
    if match.empty:
        return "科目が見つかりませんでした"

    row = match.iloc[0]
    counts = [int(row[grade]) for grade in ["A_plus_members", "A_members", "B_members", "C_members", "D_members"]]
    subject_name = row["科⽬名称"]
    subject_id = row["科⽬番号"]

    return render_template("jsgraph.html", counts=counts, subject_name=subject_name, subject_id=subject_id, year=year)

@app.route('/back', methods=['POST'])
def back():
    return render_template('report.html')

if __name__ == '__main__':
    app.run(debug=True)
