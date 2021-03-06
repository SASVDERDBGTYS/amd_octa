import os
from pathlib import Path

from config.load_config import get_config
from preprocess import preprocess
from model import get_model, get_callbacks, get_model_binary
from utils.io_funcs import *
from plotting import plot_norm_conf_matrix, plot_raw_conf_matrix, plot_training_loss, plot_training_acc


# Configuring the files here for now
cfg = get_config(filename=Path(os.getcwd()) / 'config' / 'default_config.yml')
cfg.d_data = Path('/home/jyao/local/data/orig/amd_octa/')
cfg.d_model = Path('/home/jyao/local/data/orig/amd_octa/trained_models/')

cfg.str_healthy = 'Normal'
cfg.str_dry_amd = 'Dry AMD'
cfg.str_cnv = 'CNV'

cfg.binary_class = True
cfg.binary_mode = 1     # binary_mode = 0 (normal vs NNV) / 1 (normal vs NV) / 2 (NNV vs NV)
cfg.num_classes = 2
if cfg.binary_mode == 0:
    cfg.label_healthy = 0
    cfg.label_dry_amd = 1
    cfg.vec_str_labels = ['Normal', 'NNV AMD']

elif cfg.binary_mode == 1:
    cfg.label_healthy = 0
    cfg.label_cnv = 1
    cfg.vec_str_labels = ['Normal', 'NV AMD']

elif cfg.binary_mode == 2:
    cfg.label_dry_amd = 0
    cfg.label_cnv = 1
    cfg.vec_str_labels = ['NNV AMD', 'NV AMD']

else:
    raise Exception('Undefined binary mode')

cfg.num_octa = 5
cfg.str_angiography = 'Angiography'
cfg.str_structure = 'Structure'
cfg.str_bscan = 'B-Scan'

cfg.vec_str_layer = ['Deep', 'Avascular', 'ORCC', 'Choriocapillaris', 'Choroid']
cfg.dict_layer_order = {'Deep': 0,
                        'Avascular': 1,
                        'ORCC': 2,
                        'Choriocapillaris': 3,
                        'Choroid': 4}
cfg.str_bscan_layer = 'Flow'

cfg.downscale_size = [256, 256]
cfg.per_train = 0.6
cfg.per_valid = 0.2
cfg.per_test = 0.2

cfg.n_epoch = 1000
cfg.batch_size = 8
cfg.es_patience = 20
cfg.es_min_delta = 1e-5
cfg.lr = 5e-5
cfg.lam = 1e-5
cfg.overwrite = True

cfg.balanced = False
cfg.oversample = False
cfg.oversample_method = 'smote'
cfg.random_seed = 68
cfg.use_random_seed = True

vec_idx_healthy = [1, 250]
vec_idx_dry_amd = [1, 250]
vec_idx_cnv = [1, 250]

# Preprocessing
Xs, ys = preprocess(vec_idx_healthy, vec_idx_dry_amd, vec_idx_cnv, cfg)

print("\nx_train Angiography cube shape: {}".format(Xs[0][0].shape))
print("x_train Structure OCT cube shape: {}".format(Xs[0][1].shape))
print("x_train B scan shape: {}".format(Xs[0][2].shape))
print("y_train onehot shape: {}".format(ys[0].shape))

print("\nx_valid Angiography cube shape: {}".format(Xs[1][0].shape))
print("x_valid Structure OCT cube shape: {}".format(Xs[1][1].shape))
print("x_valid B scan shape: {}".format(Xs[1][2].shape))
print("y_valid onehot shape: {}".format(ys[1].shape))

print("\nx_test Angiography cube shape: {}".format(Xs[2][0].shape))
print("x_test Structure OCT cube shape: {}".format(Xs[2][1].shape))
print("x_test B scan shape: {}".format(Xs[2][2].shape))
print("y_test onehot shape: {}".format(ys[2].shape))

# Get and train model
model = get_model('arch_010', cfg)
callbacks = get_callbacks(cfg)

h = model.fit(Xs[0], ys[0], batch_size=cfg.batch_size, epochs=cfg.n_epoch, verbose=2, callbacks=callbacks,
              validation_data=(Xs[1], ys[1]), shuffle=False, validation_batch_size=Xs[1][0].shape[0])
cfg.history = h.history

# save trained models
save_model(model, cfg, overwrite=True, save_format='tf')

# plotting training history
plot_training_loss(h, cfg, save=True)
plot_training_acc(h, cfg, save=True)

# Now perform prediction
train_set_score = model.evaluate(Xs[0], ys[0], callbacks=callbacks, verbose=0)
valid_set_score = model.evaluate(Xs[1], ys[1], callbacks=callbacks, verbose=0)
test_set_score = model.evaluate(Xs[2], ys[2], callbacks=callbacks, verbose=0)

print("\nTrain set accuracy: {}".format(train_set_score[1]))
print("Valid set accuracy: {}".format(valid_set_score[1]))
print("Test set accuracy: {}".format(test_set_score[1]))

y_true = ys[-1]
y_pred = model.predict(Xs[2])
y_pred[y_pred >= 0.5] = 1
y_pred[y_pred < 0.5] = 0

cfg.y_test_true = y_true
cfg.y_test_pred = y_pred

# plot the confusion matrices
plot_raw_conf_matrix(y_true, y_pred, cfg, save=True)
plot_norm_conf_matrix(y_true, y_pred, cfg, save=True)

print('nothing')