# precompute_optimal.py - 실제 권장량 존재 조합만 계산 + 예상시간 출력

import os
import json
import itertools
import pandas as pd
from data_loader import load_all_data
from utils import extract_unique_nutrients
from multiprocessing import Pool, cpu_count, current_process
from tqdm import tqdm
import time

# 데이터 로드
products_df, recommendations_df, mapping_df = load_all_data()
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# 실제 존재하는 성별+나이 조합만 사용
valid_pairs = recommendations_df[['성별', '나이']].drop_duplicates().dropna()
nutrients = extract_unique_nutrients(recommendations_df)

def get_optimal_combinations(sex, age, max_combinations=10000, top_n=10):
    req_df = recommendations_df[
        (recommendations_df['성별'].astype(str).str.strip() == sex) &
        (recommendations_df['나이'].astype(str).str.strip() == age)
    ]
    if req_df.empty:
        return [{'추천': '해당 조건의 권장량 데이터 없음'}], {}

    indices = products_df.index
    all_results = []

    for r in range(1, 5):
        combos = list(itertools.combinations(indices, r))
        print(f"[{sex}_{age}] {r}개 조합 수: {len(combos):,}개 → 상한 {max_combinations:,} 적용")
        if len(combos) > max_combinations:
            combos = combos[:max_combinations]

        scored = []
        for i, combo in enumerate(combos):
            sub = products_df.loc[list(combo)].fillna(0)
            price = sub['1정가격 (원)'].sum()

            total = {}
            for _, row in mapping_df.iterrows():
                col, std = row['제품DB_열이름'], row['표준성분명']
                if col in sub.columns:
                    val = sub[col].sum()
                    if 'mg' in col: val *= 1000
                    total[std] = float(val)

            satisfied = 0
            over = False
            error = 0
            for nut in nutrients:
                req = req_df[req_df['성분명'].str.contains(f'{nut}.*권장')]
                limit = req_df[req_df['성분명'].str.contains(f'{nut}.*상한')]
                req_v = req['섭취량'].values[0] if not req.empty else None
                lim_v = limit['섭취량'].values[0] if not limit.empty else None
                cur = total.get(nut, 0)
                if lim_v and cur > lim_v:
                    over = True
                    break
                if req_v and cur >= req_v:
                    satisfied += 1
                    error += abs(cur - req_v)

            if not over:
                scored.append((satisfied, error, combo, total, float(price), r))

        scored.sort(key=lambda x: (-x[0], x[1]))
        top_results = scored[:top_n]
        all_results.extend(top_results)

    if not all_results:
        return [{'추천': '조건을 만족하는 조합이 없습니다.'}], {}

    results = []
    for i, (satisfied, error, combo, total, price, r) in enumerate(all_results):
        results.append({
            '추천조합': f'{r}개 추천 #{i + 1}',
            '제품들': products_df.loc[list(combo)].astype(object).to_dict(orient='records'),
            '섭취합계': total,
            '총가격': price
        })
    return results, {'총합산': total}

def process_one_case(args):
    sex, age = args
    case_label = f"{sex}_{age}"
    start = time.time()
    results, comparison = get_optimal_combinations(sex, age)
    out_path = os.path.join(CACHE_DIR, f"{case_label}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "comparison_map": comparison}, f, ensure_ascii=False, indent=2)
    elapsed = time.time() - start
    return case_label, elapsed

if __name__ == "__main__":
    from multiprocessing import get_context

    all_cases = [(row['성별'], row['나이']) for _, row in valid_pairs.iterrows()]
    total_cases = len(all_cases)

    print(f"🔄 총 {total_cases}개의 유효 조합에 대해 캐시 생성 시작합니다...\n")
    total_time = 0

    with get_context("spawn").Pool(processes=min(cpu_count(), 8)) as pool:
        with tqdm(total=total_cases, desc="진행률", ncols=100) as pbar:
            for result, elapsed in pool.imap_unordered(process_one_case, all_cases):
                pbar.set_description(f"생성 중: {result}")
                pbar.set_postfix_str(f"{elapsed:.1f}s")
                pbar.update(1)
                total_time += elapsed

    avg_time = total_time / total_cases if total_cases else 0
    print(f"\n🎉 전체 캐시 생성 완료! 평균 시간: {avg_time:.1f}초 × {total_cases}개 ≈ {total_time/60:.1f}분")
