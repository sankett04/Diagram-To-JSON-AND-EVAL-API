import cv2
import pytesseract
#from textblob import TextBlob

import numpy as np

def extract_text(img, bbox):
    """Extract text/code from a node ROI, robust for math & normal text."""
    x, y, w, h = bbox
    pad = 10
    x1, y1 = max(0, x - pad), max(0, y - pad)
    x2, y2 = min(img.shape[1], x + w + pad), min(img.shape[0], y + h + pad)
    roi = img[y1:y2, x1:x2]

    # Preprocess ROI
    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    roi_resized = cv2.resize(roi_gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    # Adaptive threshold + dilation to make thin symbols thicker
    roi_bin = cv2.adaptiveThreshold(
        roi_resized, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY, 15, 8
    )
    if np.count_nonzero(roi_bin == 0) < 0.05 * roi_bin.size:
        _, roi_bin = cv2.threshold(roi_resized, 127, 255, cv2.THRESH_BINARY)
    roi_bin = cv2.dilate(roi_bin, np.ones((2, 2), np.uint8), iterations=1)

    # OCR configs for both normal + math text
    whitelist = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=<>/() '

    configs = [
    f'--oem 3 --psm 6 -c preserve_interword_spaces=1 tessedit_char_whitelist={whitelist}',
    f'--oem 3 --psm 7 -c preserve_interword_spaces=1 tessedit_char_whitelist={whitelist}',
    f'--oem 3 --psm 11 -c preserve_interword_spaces=1 tessedit_char_whitelist={whitelist}'
    ]


    text = ""
    for config in configs:
        t = pytesseract.image_to_string(roi_bin, config=config).strip()
        if len(t) > len(text):  # keep the best (longest) result
            text = t

    # Clean result
    text = text.replace("\n", " ").strip()
    return text


def clean_json(diagram_json):
    """Remove bbox, x, y from nodes and edges in diagram JSON."""
    cleaned = {"question_id": diagram_json.get("question_id"),
               "teacher_id": diagram_json.get("teacher_id"),
               "nodes": [],
               "edges": []}

    # Clean nodes
    for node in diagram_json.get("nodes", []):
        node_copy = {k: v for k, v in node.items() if k not in ["bbox", "x", "y"]}
        cleaned["nodes"].append(node_copy)

    # Clean edges
    for edge in diagram_json.get("edges", []):
        edge_copy = {k: v for k, v in edge.items() if k not in ["bbox", "x", "y"]}
        cleaned["edges"].append(edge_copy)

    return cleaned

def nearest_node(x, y, nodes, max_dist=40):
    nearest = None
    min_d = float("inf")
    for n in nodes:
        d = np.hypot(x - n["x"], y - n["y"])
        if d < min_d and d <= max_dist:
            min_d, nearest = d, n
    return nearest

def find_edges(img, nodes):
    edges = set()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

    lines = cv2.HoughLinesP(binary, 1, np.pi/180, threshold=60,
                            minLineLength=40, maxLineGap=10)

    if lines is None:
        return []

    for (x1, y1, x2, y2) in lines[:,0]:
        src = nearest_node(x1, y1, nodes)
        tgt = nearest_node(x2, y2, nodes)

        # Skip if not connected to valid nodes
        if not src or not tgt: 
            continue
        if src["id"] == tgt["id"]: 
            continue  # skip self-loops

        # Direction rule
        if abs(src["y"] - tgt["y"]) > abs(src["x"] - tgt["x"]):
            source, target = (src, tgt) if src["y"] < tgt["y"] else (tgt, src)
        else:
            source, target = (src, tgt) if src["x"] < tgt["x"] else (tgt, src)

        edges.add((source["id"], target["id"]))

    return [{"source": s, "target": t} for s, t in edges]




def image_to_json(image_path, question_id, teacher_id):
    import cv2
    import numpy as np
    
        
    import pytesseract
    from pytesseract import Output
    from PIL import Image
    
    #loading and converting image to gray
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 11, 2)
    
    #Detecting the nodes int the image
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    nodes = []

    for i, c in enumerate(contours):
        # Keep only top-level contours
        if hierarchy[0][i][3] != -1:
            continue
        
        area = cv2.contourArea(c)
        if area < 300 or area > 100000:
            continue

        approx = cv2.approxPolyDP(c, 0.04*cv2.arcLength(c, True), True)
        x, y, w, h = cv2.boundingRect(c)
        cx, cy = x + w // 2, y + h // 2  

        if len(approx) > 8: node_type = "start/end"
        elif len(approx) == 4: node_type = "process"
        elif len(approx) == 6: node_type = "decision"
        else: node_type = "unknown"

        nodes.append({"id": len(nodes)+1, "type": node_type, "bbox": [x,y,w,h],
                    "x": cx, "y": cy })

        #detecting text from nodes and storing as labels in nodes

        # for node in nodes:
        #     node["label"] = extract_text(img, node["bbox"])
            
        #Finding the edges and their source and target
    for node in nodes:
        node["label"] = extract_text(img, node["bbox"])   

    edges =[]
    edges = find_edges(img, nodes)
    # Convert back to list of dicts

    #print("Unique edges:", edges)
    graph_data = {
    "question_id" : question_id,
    "teacher_id": teacher_id,
    "nodes": nodes,
    "edges": edges
    }
    blueprint_json = clean_json(graph_data)
    
    return blueprint_json

