# GLUE Benchmark

The **General Language Understanding Evaluation (GLUE)** benchmark is a collection of nine natural language understanding tasks used to evaluate and compare NLU models.

## Tasks

| Task | Type | Metric |
|------|------|--------|
| CoLA | Acceptability | Matthews corr. |
| SST-2 | Sentiment | Accuracy |
| MRPC | Paraphrase | F1/Accuracy |
| STS-B | Similarity | Pearson/Spearman |
| QQP | Paraphrase | F1/Accuracy |
| MNLI | NLI | Accuracy |
| QNLI | QA/NLI | Accuracy |
| RTE | NLI | Accuracy |
| WNLI | Coreference | Accuracy |

## Relevance

Transformers (especially BERT and its successors) achieved state-of-the-art results on GLUE, demonstrating the effectiveness of the self-attention mechanism for language understanding.

**Source:** https://gluebenchmark.com/
