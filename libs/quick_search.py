"""Quick Sort 알고리즘 기반 정렬/검색 라이브러리."""


def quick_sort(records, key):
    """records를 key 필드 값 기준으로 quick sort하여 정렬된 새 리스트를 반환한다."""
    if len(records) <= 1:
        return list(records)

    pivot = records[len(records) // 2][key]
    less = [r for r in records if r[key] < pivot]
    equal = [r for r in records if r[key] == pivot]
    greater = [r for r in records if r[key] > pivot]

    return quick_sort(less, key) + equal + quick_sort(greater, key)


def binary_search(sorted_records, key, value):
    """key 필드 기준으로 정렬된 sorted_records에서 key == value인 레코드를 모두 이진 탐색으로 찾는다."""
    lo, hi = 0, len(sorted_records) - 1
    found_index = None

    while lo <= hi:
        mid = (lo + hi) // 2
        mid_value = sorted_records[mid][key]
        if mid_value == value:
            found_index = mid
            break
        elif mid_value < value:
            lo = mid + 1
        else:
            hi = mid - 1

    if found_index is None:
        return []

    # 동일한 값을 가진 레코드가 여러 개일 수 있으므로 좌우로 확장하여 모두 수집한다.
    results = [sorted_records[found_index]]

    i = found_index - 1
    while i >= 0 and sorted_records[i][key] == value:
        results.append(sorted_records[i])
        i -= 1

    j = found_index + 1
    while j < len(sorted_records) and sorted_records[j][key] == value:
        results.append(sorted_records[j])
        j += 1

    return results


def search_by_key(records, key, value):
    """records 중 key 필드를 가진 항목만 대상으로 quick sort 후 이진 탐색하여 일치하는 레코드를 찾는다."""
    candidates = [r for r in records if key in r]
    sorted_candidates = quick_sort(candidates, key)
    return binary_search(sorted_candidates, key, value)
