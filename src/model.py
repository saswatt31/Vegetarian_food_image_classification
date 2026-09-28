"""Model definitions (re-exported from dataset.py for the requested layout).

The canonical definitions live in dataset.py so train/evaluate/predict share
one source of truth:
  * build_model(num_classes)      -> frozen ImageNet ResNet-18 + new head
  * unfreeze_late_layers(model)   -> stage-2 fine-tuning helper
"""
from dataset import (  # noqa: F401
    DEVICE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    INPUT_SIZE,
    build_model,
    eval_transform,
    make_loaders,
    train_transform,
    unfreeze_late_layers,
)
