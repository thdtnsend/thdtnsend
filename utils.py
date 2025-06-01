def get_age_range(age):
    if age <= 0.5:
        return "0-5개월"
    elif age <= 1:
        return "6-11개월"
    elif age <= 2:
        return "1-2세"
    elif age <= 5:
        return "3-5세"
    elif age <= 8:
        return "6-8세"
    elif age <= 11:
        return "9-11세"
    elif age <= 14:
        return "12-14세"
    elif age <= 18:
        return "15-18세"
    elif age <= 29:
        return "19-29세"
    elif age <= 49:
        return "30-49세"
    elif age <= 64:
        return "50-64세"
    elif age <= 74:
        return "65-74세"
    else:
        return "75세 이상"

def normalize_gender(gender):
    if gender == "남성":
        return "남자"
    elif gender == "여성":
        return "여자"
    return gender

def extract_unique_nutrients(recommendations_df):
    return sorted(set(recommendations_df["성분명"].str.extract(r'(.*?)(?:_권장량|_상한량)')[0].dropna()))
