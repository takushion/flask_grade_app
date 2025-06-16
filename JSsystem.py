from flask import Flask, render_template, request, jsonify # jsonify をインポート
import pandas as pd
import traceback # スタックトレース出力用に追加
import unicodedata # 正規化および全角文字やアルファベットに対応
import re

app = Flask(__name__)

# JSsystem.py の normalize_keyword 関数を全文字対応に改良
def normalize_keyword(word):
    if not word:
        return ""
    
    # 文字列に変換
    word = str(word)
    
    # NFKC正規化（互換文字を標準文字に変換）
    # これにより、全角英数字→半角、互換漢字→標準漢字、合成文字→分解文字など
    # すべての互換文字が標準形に統一されます
    word = unicodedata.normalize('NFKC', word)
    
    word = unicodedata.normalize('NFC', word)
    
    # 制御文字や不可視文字を削除
    word = ''.join(char for char in word if unicodedata.category(char)[0] != 'C')
    
    # 大文字変換（英数字用）
    word = word.upper()
    
    # 前後の空白削除と連続空白の正規化
    word = re.sub(r'\s+', ' ', word.strip())
    
    return word

def normalize_all_text(text):
    return normalize_keyword(str(text) if text is not None else "")

def load_data(year_sheet="average"):
    """指定されたシートからExcelファイルのデータを読み込みます。"""
    try:
        df = pd.read_excel("date/grades_full.xlsx", sheet_name=year_sheet)
        # 科目番号列は文字列として扱うことを保証（Excel内で数値でも文字列に統一）
        if "科⽬番号" in df.columns:
            df["科⽬番号"] = df["科⽬番号"].astype(str)
        return df
    except FileNotFoundError:
        print(f"エラー: ファイル 'date/grades_full.xlsx' が見つかりませんでした。")
        return pd.DataFrame()
    except Exception as e:
        print(f"シート '{year_sheet}' からのデータ読み込みエラー: {e}")
        print(traceback.format_exc()) # 詳細なスタックトレースを出力
        return pd.DataFrame()

@app.route("/report.html")
def report():
    return render_template("report.html")

@app.route('/keyword', methods=['POST'])
def keyword():
    search_type = request.form['search_type']
    keyword_val = request.form['word'].strip()
    
    # 検索語を完全正規化
    normalized_keyword = normalize_keyword(keyword_val)
    
    
    df_search = load_data("average") 

    if df_search.empty:
        return render_template('result.html', results=[], count=0, error="成績データを読み込めませんでした。ファイルまたは「average」シートを確認してください。")

    if search_type == "title":
        if "科⽬名称" not in df_search.columns:
            return render_template('result.html', results=[], count=0, error="「科⽬名称」列が見つかりません。")
        
        # データベース内の全てのapplyで科目名の値全てを正規化
        df_search['normalized_subject'] = df_search["科⽬名称"].apply(normalize_all_text)
        
        # 正規化済みデータで部分一致検索
        matches = df_search[
            df_search['normalized_subject'].str.contains(
                normalized_keyword, 
                case=False,  # 大文字小文字を区別しない
                na=False, 
                regex=False  # 正規表現を無効化
            )
        ]
        
    else: # search_type == "id" (科目番号)
        if "科⽬番号" not in df_search.columns:
            return render_template('result.html', results=[], count=0, error="「科⽬番号」列が見つかりません。")
        
        # 科目番号も全て正規化して検索
        df_search['normalized_id'] = df_search["科⽬番号"].astype(str).apply(normalize_all_text)
        
        matches = df_search[
            df_search['normalized_id'].str.contains(
                normalized_keyword, 
                case=False, 
                na=False, 
                regex=False
            )
        ]

    # 正規化用の一時列を削除（結果には含めない）
    if 'normalized_subject' in matches.columns:
        matches = matches.drop('normalized_subject', axis=1)
    if 'normalized_id' in matches.columns:
        matches = matches.drop('normalized_id', axis=1)

    results = matches.to_dict(orient='records')
    count = len(results)

    return render_template('result.html', results=results, count=count)

@app.route('/graph/<subject_id>')
def show_graph(subject_id):
    year = request.args.get('year', 'average') 
    df_graph = load_data(year)

    if df_graph.empty:
        return f"指定された年度 ({year}) の科目データが見つかりませんでした。"
    
    if "科⽬番号" not in df_graph.columns:
        return "科目データ内に「科⽬番号」列が見つかりませんでした。"

    # load_dataで科目番号は文字列に変換済みのため、subject_idも文字列で比較
    match = df_graph[df_graph["科⽬番号"] == str(subject_id)]
    if match.empty:
        return f"科目ID '{subject_id}' が年度 '{year}' に見つかりませんでした。"

    row = match.iloc[0]
    grade_columns = ["A_plus_members", "A_members", "B_members", "C_members", "D_members"]
    counts = []
    for col in grade_columns:
        if col in row and pd.notna(row[col]):
            try:
                counts.append(int(row[col]))
            except ValueError:
                counts.append(0)
        else:
            counts.append(0)
            
    subject_name_col = "科⽬名称"
    subject_name = str(row[subject_name_col]) if subject_name_col in row else "名称不明"


    return render_template("jsgraph.html", counts=counts, subject_name=subject_name, subject_id=subject_id, year=year)

@app.route('/back', methods=['POST'])
def back():
    return render_template('report.html')

@app.route('/bookmarks')
def bookmarks_page():
    return render_template('bookmarks.html')

@app.route('/api/subject_grade_data/<subject_id>')
def subject_grade_data(subject_id):
    year = request.args.get('year', 'average')
    print(f"[API INFO] Request received for subject_id: {subject_id}, year: {year}")

    df_data = load_data(year)

    if df_data.empty:
        print(f"[API ERROR] Data for year '{year}' not found or empty.")
        return jsonify({"error": f"年度 '{year}' のデータが見つからないか空です。"}), 404

    required_columns = ["科⽬番号", "科⽬名称", "A_plus_members", "A_members", "B_members", "C_members", "D_members"]
    missing_df_cols = [col for col in required_columns if col not in df_data.columns and col in ["科⽬番号", "科⽬名称"]] # 主要な列の存在チェック
    if missing_df_cols:
        err_msg = f"データシート '{year}' に必須列が見つかりません: {', '.join(missing_df_cols)}"
        print(f"[API ERROR] {err_msg}")
        return jsonify({"error": err_msg}), 500
    
    # load_dataで科目番号は文字列に変換済みのため、subject_idも文字列で比較
    try:
        match = df_data[df_data["科⽬番号"] == str(subject_id)]
    except Exception as e:
        err_msg = f"科目番号のマッチング中に予期せぬエラー: {e}"
        print(f"[API ERROR] {err_msg}\n{traceback.format_exc()}")
        return jsonify({"error": err_msg}), 500

    if match.empty:
        err_msg = f"科目ID '{subject_id}' が年度 '{year}' に見つかりません。"
        print(f"[API INFO] {err_msg}") # これはエラーではなく情報の場合もある
        return jsonify({"error": err_msg}), 404

    row = match.iloc[0]
    
    counts = []
    grade_columns = ["A_plus_members", "A_members", "B_members", "C_members", "D_members"]
    for col in grade_columns:
        if col in row and pd.notna(row[col]):
            try:
                counts.append(int(float(row[col]))) # Excelで数値が浮動小数点数として読まれる場合も考慮
            except ValueError:
                counts.append(0)
                print(f"[API WARNING] Subject {subject_id}, Year {year}, Column {col}: Invalid value for int conversion '{row[col]}'. Defaulting to 0.")
        else:
            counts.append(0)
            if col not in row:
                print(f"[API WARNING] Subject {subject_id}, Year {year}: Grade column '{col}' not found. Defaulting to 0.")

    subject_name = str(row["科⽬名称"]) if "科⽬名称" in row else "名称不明"
    actual_subject_id = str(row["科⽬番号"]) if "科⽬番号" in row else subject_id # 念のため

    response_data = {
        "subject_name": subject_name,
        "subject_id": actual_subject_id, 
        "year": year,
        "counts": counts
    }
    print(f"[API INFO] Successfully prepared data for subject_id: {subject_id}, year: {year}. Data: {response_data}")
    return jsonify(response_data)

@app.route('/summary')
def summary_page():
    # URLから並べ替えモードを取得 (例: /summary?sort=gpa)
    # パラメータがなければ 'file' (ファイル順) をデフォルトとします
    sort_mode = request.args.get('sort', 'file')

    df = load_data("average")

    if df.empty:
        return render_template('summary.html', results=[], count=0, error="成績データを読み込めませんでした。")

    # GPA計算に必要な人数カラムのリスト
    member_columns = [
        "A_plus_members", "A_members", "B_members", "C_members", "D_members", "full_members"
    ]

    # 必要な列が存在するか確認し、なければ0で埋めます
    for col in member_columns:
        if col not in df.columns:
            print(f"[GPA WARNING] Column '{col}' not found. GPA calculation might be inaccurate.")
            df[col] = 0
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # GPAを計算します
    total_points = (
        df["A_plus_members"] * 4.3 +
        df["A_members"] * 4.0 +
        df["B_members"] * 3.0 +
        df["C_members"] * 2.0
    )
    df['gpa'] = total_points.div(df['full_members']).where(df['full_members'] > 0, 0)

    # 並べ替えモードに応じてソートを実行します
    if sort_mode == 'gpa':
        # 성적순(成績順)の場合はGPAで降順（高い順）にソート
        df = df.sort_values(by='gpa', ascending=False)
    # sort_modeが'file'の場合、または指定がない場合は何もしない（ファイル順のまま）

    # テンプレートに渡すデータを準備します
    df = df.astype(object).where(pd.notnull(df), None)
    results = df.to_dict(orient='records')
    count = len(results)

    # 現在の並べ替えモードをテンプレートに渡します
    return render_template('summary.html',
                        results=results,
                        count=count,
                        current_sort=sort_mode,
                        error=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
