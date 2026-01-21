---
library_name: peft
base_model: raflisbk/t5-posting-time-summarizer
tags:
- base_model:adapter:raflisbk/t5-posting-time-summarizer
- lora
- transformers
model-index:
- name: t5-posting-time-summarizer
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# t5-posting-time-summarizer

This model is a fine-tuned version of [raflisbk/t5-posting-time-summarizer](https://huggingface.co/raflisbk/t5-posting-time-summarizer) on the None dataset.
It achieves the following results on the evaluation set:
- Loss: 1.3803

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 0.0001
- train_batch_size: 4
- eval_batch_size: 4
- seed: 42
- gradient_accumulation_steps: 4
- total_train_batch_size: 16
- optimizer: Use OptimizerNames.PAGED_ADAMW_8BIT with betas=(0.9,0.999) and epsilon=1e-08 and optimizer_args=No additional optimizer arguments
- lr_scheduler_type: cosine
- lr_scheduler_warmup_ratio: 0.15
- num_epochs: 10

### Training results

| Training Loss | Epoch | Step | Validation Loss |
|:-------------:|:-----:|:----:|:---------------:|
| 3.2863        | 1.0   | 18   | 2.7599          |
| 2.7887        | 2.0   | 36   | 2.0891          |
| 2.166         | 3.0   | 54   | 1.7194          |
| 1.8545        | 4.0   | 72   | 1.5583          |
| 1.7343        | 5.0   | 90   | 1.4826          |
| 1.6687        | 6.0   | 108  | 1.4305          |
| 1.6589        | 7.0   | 126  | 1.4013          |
| 1.587         | 8.0   | 144  | 1.3864          |
| 1.5626        | 9.0   | 162  | 1.3813          |
| 1.5749        | 10.0  | 180  | 1.3803          |


### Framework versions

- PEFT 0.17.1
- Transformers 4.57.1
- Pytorch 2.8.0+cu126
- Datasets 4.4.2
- Tokenizers 0.22.1