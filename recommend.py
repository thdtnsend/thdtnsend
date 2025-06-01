import os
import json

UNIT_MAPPING = {
    "비타민 A": ("μg", "μg RAE"), "비타민 D": ("μg", "μg"),
    "비타민 E": ("μg", "mg α-TE"), "비타민 K": ("μg", "μg"),
    "티아민": ("μg", "mg"), "리보플라빈": ("μg", "mg"),
    "나이아신": ("μg", "mg NE"), "비타민B6": ("μg", "mg"),
    "엽산": ("μg", "μg DFE"), "비타민B12": ("μg", "μg"),
    "비오틴": ("μg", "μg"), "비타민C": ("μg", "mg"),
    "칼슘": ("μg", "mg"), "철": ("μg", "mg"), "아연": ("μg", "mg"),
    "셀레늄": ("μg", "μg"), "구리": ("μg", "mg"), "망간": ("μg", "mg"),
    "몰리브덴": ("μg", "μg"), "요오드": ("μg", "μg"), "마그네슘": ("μg", "mg")
}

def format_with_unit(value_ug, std_name):
    base_unit, display_unit = UNIT_MAPPING.get(std_name, ("μg", "μg"))
    if value_ug is None or value_ug == "-":
        return "-"
    if base_unit == "μg" and value_ug >= 1000:
        return f"{round(value_ug / 1000, 2)} mg"
    else:
        return f"{round(value_ug, 1)} {display_unit}"

def get_cache_filename(gender, age_range):
    return os.path.join("cache", f"{gender}_{age_range}.json")

def recommend_products(gender, age_range, products_df, recommendations_df, mapping_df, selected_nutrients, max_comb=4, max_price=100000):
    cache_file = get_cache_filename(gender, age_range)
    if not os.path.exists(cache_file):
        return [{"추천": "해당 성별과 연령에 대한 추천 캐시가 없습니다."}], {}

    with open(cache_file, "r", encoding="utf-8") as f:
        cache = json.load(f)

    filtered = []
    for entry in cache["results"]:
        product_count = len(entry["제품들"])
        if product_count > max_comb:
            continue

        # ✅ 총가격 재계산 (제품 단위의 실제 총가격)
        total_price = sum(item.get("총제품가격 (원)", 0) for item in entry["제품들"])
        if total_price > max_price:
            continue

        entry_nutrients = entry["섭취합계"]
        satisfied = 0
        error = 0

        for std_name in selected_nutrients or entry_nutrients.keys():
            req_df = recommendations_df[
                (recommendations_df["성별"] == gender) &
                (recommendations_df["나이"].astype(str).str.strip() == age_range) &
                (recommendations_df["성분명"].str.contains(f"{std_name}.*권장"))
            ]
            req_val = req_df["섭취량"].values[0] if not req_df.empty else None
            cur_val = entry_nutrients.get(std_name, 0)

            if req_val and cur_val >= req_val:
                satisfied += 1
                error += abs(cur_val - req_val)

        filtered.append((satisfied, error, entry, total_price))

    if not filtered:
        return [{"추천": "입력 조건을 만족하는 조합이 없습니다."}], {}

    filtered.sort(key=lambda x: (-x[0], x[1]))

    final_result = []
    comparison_map = {}

    for idx, (satisfied, error, r, total_price) in enumerate(filtered[:5]):
        tag = f"추천 #{idx + 1}"

        result_entry = {
            "추천조합": tag,
            "제품명목록": [item["제품명"] for item in r["제품들"]],
            "총가격": total_price  # ✅ 실제 총제품가격 합산된 값
        }

        final_result.append(result_entry)

        comparison = []
        for std_name in selected_nutrients or r["섭취합계"].keys():
            권장 = recommendations_df[
                (recommendations_df["성별"] == gender) &
                (recommendations_df["나이"].astype(str).str.strip() == age_range) &
                (recommendations_df["성분명"].str.contains(f"{std_name}.*권장"))
            ]
            상한 = recommendations_df[
                (recommendations_df["성별"] == gender) &
                (recommendations_df["나이"].astype(str).str.strip() == age_range) &
                (recommendations_df["성분명"].str.contains(f"{std_name}.*상한"))
            ]
            권장값 = 권장["섭취량"].values[0] if not 권장.empty else None
            상한값 = 상한["섭취량"].values[0] if not 상한.empty else None
            섭취값 = r["섭취합계"].get(std_name, 0)
            상한여부 = "초과" if 상한값 and 섭취값 > 상한값 else "안전"

            comparison.append({
                "성분명": std_name,
                "섭취량": format_with_unit(섭취값, std_name),
                "권장섭취량": format_with_unit(권장값, std_name),
                "권장 충족 여부": "✔" if 권장값 and 섭취값 >= 권장값 else "✘",
                "상한섭취량": format_with_unit(상한값, std_name),
                "상한 초과 여부": 상한여부
            })

        comparison_map[tag] = comparison

    return final_result, comparison_map
