import os
import json
import logging
import datetime
from typing import Dict, Any
from collections import defaultdict
from rouge_score import rouge_scorer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Initialize the scorer once
scorer = rouge_scorer.RougeScorer(['rougeL','rougeLsum'], use_stemmer=True)

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"File not found: {path}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON in file: {path}")
        return None
    except Exception as e:
        logging.error(f"Error loading {path}: {e}")
        return None

def f1_score_list(gt_list, pred_list):
    # Lowercase all string elements for case-insensitive comparison
    gt_set = set([x.lower() if isinstance(x, str) else x for x in gt_list])
    pred_set = set([x.lower() if isinstance(x, str) else x for x in pred_list])
    if not gt_set and not pred_set:
        return 1.0
    tp = len(gt_set & pred_set)
    fp = len(pred_set - gt_set)
    fn = len(gt_set - pred_set)
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)

def rouge_similarity(a, b):
    if a is None and b is None:
        return 1.0
    if a is None or b is None:
        return 0.0
    
    scores = scorer.score(str(a), str(b))
    return scores['rougeLsum'].fmeasure

def compare_value_field(field, gt_val, pred_val):
    # For booleans, check type and compare directly
    if field in ["currently_unavoidable", "intentionally_added"]:
        if not (isinstance(gt_val, bool) or gt_val is None):
            logging.warning(f"GT value for '{field}' is not boolean or None: {gt_val}")
        if not (isinstance(pred_val, bool) or pred_val is None):
            logging.warning(f"Pred value for '{field}' is not boolean or None: {pred_val}")
        return float(gt_val == pred_val)
    # For lists, use F1
    elif field in ["who", "action", "products", "exceptions"]:
        return f1_score_list(gt_val or [], pred_val or [])
    # For title, use ROUGE
    elif field == "title":
        return rouge_similarity(gt_val, pred_val)
    # For other strings, use case-insensitive exact match
    elif isinstance(gt_val, str) or isinstance(pred_val, str):
        gt_val = gt_val.lower() if isinstance(gt_val, str) else gt_val
        pred_val = pred_val.lower() if isinstance(pred_val, str) else pred_val
        return float(gt_val == pred_val)
    # Fallback to direct comparison
    else:
        return float(gt_val == pred_val)


def compare_provenance_field(gt_prov, pred_prov):
    return rouge_similarity(gt_prov, pred_prov)

def compare_regulation_combined(gt: Dict[str, Any], pred: Dict[str, Any]):
    value_scores = {}
    provenance_scores = {}
    fields = ["type", "date", "who", "products"]#["type", "date", "who", "action", "products", "exceptions", "currently_unavoidable", "intentionally_added"]

    for field in fields:
        if field =="type" and "type" not in pred.keys():
            _field = "reg_type"
        else:
            _field = field

        # Handle missing field or non-dict structure in prediction
        if not isinstance(pred.get(_field), dict):
            

            # If _field exists but not in correct format, get direct value
            gt_val = gt.get(field, {}).get("value") if isinstance(gt.get(field), dict) else gt.get(field)
            pred_val = pred.get(_field)

            value_scores[field] = compare_value_field(field, gt_val, pred_val)
            provenance_scores[field] = 0.0  # No provenance score if structure is wrong
            continue



        else:
            pred_val = pred.get(_field, {}).get("value")
            pred_prov = pred.get(_field, {}).get("provenance")
        # Handle value comparison

        gt_val = gt.get(field, {}).get("value")

        value_scores[field] = compare_value_field(field, gt_val, pred_val)

        # Handle provenance comparison
        gt_prov = gt.get(field, {}).get("provenance")
        
        provenance_scores[field] = compare_provenance_field(gt_prov, pred_prov)

    return value_scores, provenance_scores

def compare_code_combined(gt: Dict[str, Any], pred: Dict[str, Any]) -> Dict[str, float]:
    scores = {}
    provenance_fields = ["title", "location", "reference", "status", "date", "pfas_definition"]#["status", "pfas_definition"]
    value_fields = ["title", "location", "reference", "status", "date", "pfas_definition"]

    for field in value_fields:
        # Handle value comparison with flexible structure
        gt_val = gt.get(field, {}).get("value") if isinstance(gt.get(field), dict) else gt.get(field)
        pred_val = pred.get(field, {}).get("value") if isinstance(pred.get(field), dict) else pred.get(field)
        if (field == "pfas_definition") and ('mpart'in pred_val):
            pred_val = 'single_fluorinated_carbon'
        scores[f"{field}_value"] = compare_value_field(field, gt_val, pred_val)


        # Handle provenance fields
        if field in provenance_fields:
            gt_prov = gt.get(field, {}).get("provenance") if isinstance(gt.get(field), dict) else None
            
            # Handle case where prediction field exists but isn't in correct format
            if not isinstance(pred.get(field), dict):
                scores[f"{field}_provenance"] = 0.0
                continue
            
            pred_prov = pred.get(field, {}).get("provenance")
            scores[f"{field}_provenance"] = compare_provenance_field(gt_prov, pred_prov)

    # Regulations (as before)
    gt_regs = gt.get("regulations", [])
    pred_regs = pred.get("regulations", [])
    value_reg_scores = []
    prov_reg_scores = []
    type_value_reg_scores = []
    type_prov_reg_scores = []
    who_value_reg_scores = []
    who_prov_reg_scores = []
    date_value_reg_scores = []
    date_prov_reg_scores = []
    prod_value_reg_scores = []
    prod_prov_reg_scores = []
    matched = set()
    for i, gt_reg in enumerate(gt_regs):
        best_score = 0
        best_prov_score = 0
        best_pred_idx = -1
        best_value_field_scores = None
        best_prov_field_scores = None
        best_type_value = 0
        best_type_prov = 0
        best_who_value = 0
        best_who_prov = 0
        best_date_value = 0
        best_date_prov = 0
        best_prod_value = 0
        best_prod_prov = 0
        for idx, pred_reg in enumerate(pred_regs):
            if idx in matched:
                continue
            value_field_scores, prov_field_scores = compare_regulation_combined(gt_reg, pred_reg)
            value_score = sum(value_field_scores.values()) / len(value_field_scores)
            prov_score = sum(prov_field_scores.values()) / len(prov_field_scores)

            if value_score > best_score:
                best_score = value_score
                best_prov_score = prov_score
                best_pred_idx = idx
                best_value_field_scores = value_field_scores
                best_prov_field_scores = prov_field_scores
                best_type_value = value_field_scores['type']
                best_type_prov = prov_field_scores['type']
                best_who_value = value_field_scores['who']
                best_who_prov = prov_field_scores['who']
                best_date_value = value_field_scores['date']
                best_date_prov = prov_field_scores['date']
                best_prod_value = value_field_scores['products']
                best_prod_prov = prov_field_scores['products']

        if best_pred_idx >= 0:
            matched.add(best_pred_idx)
        value_reg_scores.append(best_score)
        prov_reg_scores.append(best_prov_score)
        type_value_reg_scores.append(best_type_value)
        type_prov_reg_scores.append(best_type_prov)
        who_value_reg_scores.append(best_who_value)
        who_prov_reg_scores.append(best_who_prov)
        date_value_reg_scores.append(best_date_value)
        date_prov_reg_scores.append(best_date_prov)
        prod_value_reg_scores.append(best_prod_value)
        prod_prov_reg_scores.append(best_prod_prov)

        logging.info(f"Regulation {i+1}:")
        logging.info(f"  Value field scores: {best_value_field_scores}")
        logging.info(f"  Provenance field scores: {best_prov_field_scores}")
        logging.info(f"  Value score: {best_score:.3f}")
        logging.info(f"  Provenance score: {best_prov_score:.3f}")
    
    num_matched = len(matched)
    num_gt = len(gt_regs)
    num_pred = len(pred_regs)
    precision = num_matched / num_pred if num_pred > 0 else 0.0
    recall = num_matched / num_gt if num_gt > 0 else 0.0
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0
    scores["regulations_match_precision"] = precision
    scores["regulations_match_recall"] = recall
    scores["regulations_match_f1"] = f1

    scores["regulations_value_avg_score"] = sum(value_reg_scores) / len(gt_regs) if gt_regs else 1.0
    scores["regulations_provenance_avg_score"] = sum(prov_reg_scores) / len(gt_regs) if gt_regs else 1.0
    scores["regulations_type_value_avg_score"] = sum(type_value_reg_scores) / len(type_value_reg_scores) if gt_regs else 1.0
    scores["regulations_type_provenance_avg_score"] = sum(type_prov_reg_scores) / len(type_prov_reg_scores) if gt_regs else 1.0
    scores["regulations_who_value_avg_score"] = sum(who_value_reg_scores) / len(who_value_reg_scores) if gt_regs else 1.0
    scores["regulations_who_provenance_avg_score"] = sum(who_prov_reg_scores) / len(who_prov_reg_scores) if gt_regs else 1.0
    scores["regulations_date_value_avg_score"] = sum(date_value_reg_scores) / len(date_value_reg_scores) if gt_regs else 1.0
    scores["regulations_date_provenance_avg_score"] = sum(date_prov_reg_scores) / len(date_prov_reg_scores) if gt_regs else 1.0
    scores["regulations_products_value_avg_score"] = sum(prod_value_reg_scores) / len(prod_value_reg_scores) if gt_regs else 1.0
    scores["regulations_products_provenance_avg_score"] = sum(prod_prov_reg_scores) / len(prod_prov_reg_scores) if gt_regs else 1.0
    scores["num_pred_regulations"] = len(pred_regs)
    return scores

def evaluate_folder(gt_folder, pred_folder, output_path=None):
    """Evaluate all predictions in pred_folder against ground truth in gt_folder.

    Args:
        gt_folder:   Path to the golden dataset folder (document-NN.json files).
        pred_folder: Path to a model output subfolder (document-NN.json files).
        output_path: Optional path for the results file. Defaults to
                     evaluation_results_<pred_folder_name>_<timestamp>.txt
                     in the current directory.
    """
    if output_path is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pred_folder_name = os.path.basename(os.path.normpath(pred_folder))
        output_path = f"evaluation_results_{pred_folder_name}_{timestamp}.txt"

    file_handler = logging.FileHandler(output_path, mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logging.getLogger().addHandler(file_handler)

    results = []
    for fname in sorted(os.listdir(gt_folder)):
        if not fname.endswith(".json"):
            continue
        gt_path = os.path.join(gt_folder, fname)
        pred_path = os.path.join(pred_folder, fname)
        logging.info(f"Evaluating {fname}...")

        if not os.path.exists(pred_path):
            logging.warning(f"Prediction missing for {fname}")
            continue
        gt = load_json(gt_path)
        pred = load_json(pred_path)
        if gt is None or pred is None:
            logging.warning(f"Skipping {fname} due to loading error.")
            continue
        scores = compare_code_combined(gt, pred)
        results.append((fname, scores))

    # Per-file results
    lines = []
    for fname, scores in results:
        lines.append(f"\n=== Results for {fname} ===")
        for k, v in scores.items():
            lines.append(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}")

    # Aggregated averages
    agg = defaultdict(list)
    for _, scores in results:
        for k, v in scores.items():
            agg[k].append(v)
    lines.append("\n=== Evaluation Results (Averages) ===")
    for k, v in agg.items():
        lines.append(f"{k}: avg={sum(v)/len(v):.3f}")

    with open(output_path, "a") as f:
        for line in lines:
            f.write(line + "\n")

    logging.getLogger().removeHandler(file_handler)
    file_handler.close()

    logging.info(f"Results saved to {output_path}")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate model output against the golden dataset.")
    parser.add_argument("pred_folder", help="Path to a model output subfolder containing document-NN.json files.")
    parser.add_argument("--gt_folder", default="golden_dataset_json", help="Path to the golden dataset folder (default: golden_dataset_json).")
    parser.add_argument("--output", default=None, help="Path for the results .txt file (optional).")
    args = parser.parse_args()

    evaluate_folder(args.gt_folder, args.pred_folder, args.output)