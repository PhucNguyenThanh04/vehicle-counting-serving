def center_bbox(bbox):
    x1, y1, x2, y2 = bbox
    x_center = (x1 + x2) /2
    y_center = (y1 + y2) /2

    return x_center, y_center

def get_foot_position(bbox):
    x1, y1, x2, y2 = bbox
    return int((x1+x2)/2), int(y2)