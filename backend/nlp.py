from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from math import radians, sin, cos, sqrt, atan2
from datetime import datetime


def build_text(report):
    parts = [
        report.get("category", ""),
        report.get("color", ""),
        report.get("brand", ""),
        report.get("description", "")
    ]

    return " ".join(
        str(x) for x in parts
        if x is not None and str(x).strip()
    ).strip()


def calculate_distance(lat1, lon1, lat2, lon2):
    try:
        if lat1 is None or lon1 is None:
            return None

        if lat2 is None or lon2 is None:
            return None

        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)

        earth_radius = 6371.0

        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)

        a = (
            sin(dlat / 2) ** 2
            + cos(radians(lat1))
            * cos(radians(lat2))
            * sin(dlon / 2) ** 2
        )

        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return earth_radius * c

    except Exception:
        return None


def calculate_location_score(lost_report, found_report):
    distance = calculate_distance(
        lost_report.get("latitude"),
        lost_report.get("longitude"),
        found_report.get("latitude"),
        found_report.get("longitude")
    )

    if distance is None:
        return 0.0, None

    if distance <= 0.2:
        score = 1.0
    elif distance <= 1:
        score = 0.8
    elif distance <= 3:
        score = 0.5
    else:
        score = 0.2

    return score, round(distance, 3)


def parse_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def calculate_time_difference(lost_report, found_report):
    lost_time = parse_datetime(
        lost_report.get("date_time")
    )

    found_time = parse_datetime(
        found_report.get("date_time")
    )

    if lost_time is None or found_time is None:
        return None

    try:
        difference = abs(found_time - lost_time)

        return difference.total_seconds() / 60

    except Exception:
        return None


def calculate_time_score(lost_report, found_report):
    difference = calculate_time_difference(
        lost_report,
        found_report
    )

    if difference is None:
        return 0.0, None

    if difference <= 30:
        score = 1.0
    elif difference <= 120:
        score = 0.8
    elif difference <= 1440:
        score = 0.5
    else:
        score = 0.2

    return score, round(difference, 1)


def calculate_text_scores(lost_report, found_reports):
    lost_text = build_text(lost_report)

    found_texts = [
        build_text(report)
        for report in found_reports
    ]

    # If there are no usable descriptions,
    # return zero scores instead of crashing.
    if not lost_text or not any(found_texts):
        return [0.0] * len(found_reports)

    try:
        all_texts = [lost_text] + found_texts

        vectorizer = TfidfVectorizer()

        matrix = vectorizer.fit_transform(all_texts)

        scores = cosine_similarity(
            matrix[0:1],
            matrix[1:]
        ).flatten()

        return [
            float(score)
            for score in scores
        ]

    except Exception:
        return [0.0] * len(found_reports)


def rank_found_reports(lost_report, found_reports):

    if not found_reports:
        return []

    text_scores = calculate_text_scores(
        lost_report,
        found_reports
    )

    results = []

    for index, report in enumerate(found_reports):

        location_score, distance = (
            calculate_location_score(
                lost_report,
                report
            )
        )

        time_score, time_difference = (
            calculate_time_score(
                lost_report,
                report
            )
        )

        text_score = text_scores[index]

        # Attribute score
        attribute_matches = 0
        attribute_total = 0

        for field in ["category", "color", "brand"]:

            lost_value = str(
                lost_report.get(field, "")
            ).strip().lower()

            found_value = str(
                report.get(field, "")
            ).strip().lower()

            if lost_value:
                attribute_total += 1

                if lost_value == found_value:
                    attribute_matches += 1

        if attribute_total > 0:
            attribute_score = (
                attribute_matches / attribute_total
            )
        else:
            attribute_score = 0.0

        # Final combined score
        final_score = (
            0.35 * text_score
            + 0.15 * location_score
            + 0.10 * time_score
            + 0.40 * attribute_score
        )

        result = dict(report)

        result["text_score"] = round(
            text_score,
            4
        )

        result["location_score"] = round(
            location_score,
            4
        )

        result["distance_km"] = distance

        result["time_score"] = round(
            time_score,
            4
        )

        result["time_difference_minutes"] = (
            time_difference
        )

        result["attribute_score"] = round(
            attribute_score,
            4
        )

        result["final_score"] = round(
            final_score,
            4
        )

        results.append(result)

    # Highest matching score first
    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return results