from rapidfuzz import fuzz
from collections import defaultdict, deque
import math
import os
import json


# Keyword matching
def keyword_match(student_nodes, teacher_nodes):
    matches = 0
    matched_labels = []
    missing_labels = []

    for t in teacher_nodes:
        found = False
        for s in student_nodes:
            if fuzz.ratio(s["label"], t["label"]) > 80:  # fuzzy match
                matches += 1
                matched_labels.append(t["label"])
                found = True
                break
        if not found:
            missing_labels.append(t["label"])

    ratio = matches / len(teacher_nodes) if teacher_nodes else 0
    return ratio, matched_labels, missing_labels


# --- 2) Edge matching ---
def edge_match(student_json, teacher_json):
    student_edges, teacher_edges = [], []

    # Teacher edges
    for e in teacher_json["edges"]:
        s_label = next(n["label"] for n in teacher_json["nodes"] if n["id"] == e["source"])
        t_label = next(n["label"] for n in teacher_json["nodes"] if n["id"] == e["target"])
        teacher_edges.append((s_label, t_label))

    # Student edges
    for e in student_json["edges"]:
        s_label = next(n["label"] for n in student_json["nodes"] if n["id"] == e["source"])
        t_label = next(n["label"] for n in student_json["nodes"] if n["id"] == e["target"])
        student_edges.append((s_label, t_label))

    matches = sum(1 for e in teacher_edges if e in student_edges)
    ratio = matches / len(teacher_edges) if teacher_edges else 0
    missing = [e for e in teacher_edges if e not in student_edges]

    return ratio, matches, missing


# --- 3) Combined evaluation ---
def evaluate_diagram(student_json, teacher_json, weight_nodes=0.6, weight_edges=0.4):
    # Node keywords
    keyword_ratio, matched_nodes, missing_nodes = keyword_match(
        student_json["nodes"], teacher_json["nodes"]
    )

    # Edges
    edge_ratio, matched_edges, missing_edges = edge_match(student_json, teacher_json)


    results = {
        "keyword_match_ratio": round(keyword_ratio, 2),
        "edge_match_ratio": round(edge_ratio, 2),
        "matched_nodes": len(matched_nodes),
        "missing_nodes": len(missing_nodes),
    }
    return results




