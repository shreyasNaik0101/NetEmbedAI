# Model comparison

| run                              | enc | clean F1 | morph F1 | gap | params |
|----------------------------------|-----|----------|----------|-------|--------|
| tcn_contrastive                  | tcn | 0.910    | 0.268    | +0.642 | 93,930 |
| tcn_supervised                   | tcn | 0.907    | 0.206    | +0.701 | 93,930 |
| bilstm_supervised                | bilstm | 0.898    | 0.183    | +0.715 | 145,322 |
| tcn_contrastive_morph            | tcn | 0.880    | 0.764    | +0.116 | 93,930 |
