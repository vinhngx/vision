# Image classification reference training scripts

This folder contains reference training scripts for image classification.
They serve as a log of how to train specific models, as provide baseline
training and evaluation scripts to quickly bootstrap research.

Except otherwise noted, all models have been trained on 8x V100 GPUs.

### ResNext-50 32x4d
```
python -m torch.distributed.launch --nproc_per_node=8 --use_env train.py\
    --model resnext50_32x4d --epochs 100
```


### ResNext-101 32x8d

On 8 nodes, each with 8 GPUs (for a total of 64 GPUS)
```
python -m torch.distributed.launch --nproc_per_node=8 --use_env train.py\
    --model resnext101_32x8d --epochs 100
```


### MobileNetV2
```
python -m torch.distributed.launch --nproc_per_node=8 --use_env train.py\
     --model mobilenet_v2 --epochs 300 --lr 0.045 --wd 0.00004\
     --lr-step-size 1 --lr-gamma 0.98
```

## Quantized

### Parameters used for generating quantized models:

For all post training quantized models (All quantized models except mobilenet-v2), the settings are:

1. num_calibration_batches: 32
2. num_workers: 16
3. batch_size: 32
4. eval_batch_size: 128
5. backend: 'fbgemm'

For Mobilenet-v2, the model was trained with quantization aware training, the settings used are:
1. num_workers: 16
2. batch_size: 32
3. eval_batch_size: 128
4. backend: 'qnnpack'
5. learning-rate: 0.0001
6. num_epochs: 90
7. num_observer_update_epochs:4
8. num_batch_norm_update_epochs:3
9. momentum: 0.9
10. lr_step_size:30
11. lr_gamma: 0.1

Training converges at about 10 epochs.

For post training quant, device is set to CPU. For training, the device is set to CUDA
