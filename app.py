from flask import Flask, render_template, request
from utils import get_age_range, normalize_gender
from data_loader import load_all_data
from recommend import recommend_products

app = Flask(__name__)

# [1] 엑셀 데이터 로딩 (앱 실행 시 1회만)
products_df, recommendations_df, mapping_df = load_all_data()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # [2] 사용자 입력 처리
        raw_gender = request.form["gender"]         # "남성" or "여성"
        raw_age = int(request.form["age"])          # 예: 24
        max_price = int(request.form["max_price"])  # 예: 100000
        max_comb = int(request.form.get("max_comb", 4))

        # [3] 전처리: 표준화
        gender = normalize_gender(raw_gender)       # "남성" → "남자"
        age_range = get_age_range(raw_age)          # 24 → "19-29세"

        # [4] 추천 결과 및 성분 비교표 계산
        results, comparison_map = recommend_products(
            gender,
            age_range,
            products_df,
            recommendations_df,
            mapping_df,
            selected_nutrients=[],  # 전체 성분 기준 평가
            max_comb=max_comb,
            max_price=max_price
        )

        return render_template(
            "result.html",
            gender=raw_gender,
            age=raw_age,
            results=results,
            comparison_map=comparison_map
        )

    # GET 요청 시: 빈 폼 표시
    return render_template("form.html")

if __name__ == "__main__":
    app.run(debug=True)
