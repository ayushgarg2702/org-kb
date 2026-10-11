# Evaluation

Metrics are computed by scripts against golden datasets. Do not invent performance numbers.

## Dimensions

Source correctness, relationship accuracy, retrieval precision/recall, answer correctness, evidence faithfulness, abstention quality, confidence calibration, freshness, efficiency (tokens, latency, cost), security leakage.

## Datasets

`evaluation/datasets/*.yaml` — questions, expected evidence, forbidden claims, method.

## Compare configurations

Lexical-only → +symbols → +semantic → +graph → +history → +live.

Choose the cheapest configuration that meets accuracy and security gates.
