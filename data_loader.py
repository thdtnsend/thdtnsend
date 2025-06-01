import pandas as pd

def load_all_data():
    products_path = "제품.xlsx"
    recommendations_path = "정규화_권장섭취량_테이블_최종.xlsx"
    mapping_path = "성분명_매핑_테이블.xlsx"

    try:
        products_df = pd.read_excel(products_path, engine="openpyxl")
        recommendations_df = pd.read_excel(recommendations_path, engine="openpyxl")
        mapping_df = pd.read_excel(mapping_path, engine="openpyxl")

        return products_df, recommendations_df, mapping_df

    except Exception as e:
        print(f"파일 로딩 오류: {e}")
        return None, None, None
