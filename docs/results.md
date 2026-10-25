# Results

## Subject detection

YOLO11n fine-tuned on HomeObjects-3K (12 classes; 2,285 training
and 404 validation images), measured on the validation set:

| Precision | Recall | mAP50 | mAP50-95 |
| --- | --- | --- | --- |
| about 0.71 | 0.60 | 0.65 | 0.44 |

Precision is the share of detections that were right, recall the share of real objects
found; mAP50 and mAP50-95 are the standard detection scores at a loose and a strict
overlap threshold. The mean recall across the 12 classes is 67.7%.

The confusion matrix below shows how often each class was mistaken for each other class.
Windows and doors score lowest, and the bottom row counts the objects the model missed
entirely.

<p align="center">
  <img src="media/yolo-confusion.jpg" width="560" alt="Normalised confusion matrix for the 12 household object classes; the diagonal ranges from 0.48 for door to 0.79 for photo frame">
</p>

## Framing on the real camera

On this hardware, with the drone on the ground and moved
by hand, CINE cut the subject's average distance from its rule-of-thirds target from
127.6 px to 32.5 px. The flight results are in
[CINE](https://github.com/Kino-Studios/CINE/blob/main/docs/results.md); they come from simulation.
