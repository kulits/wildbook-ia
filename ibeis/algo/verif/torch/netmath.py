import utool as ut
import numpy as np
import vtool as vt
import six
import torch
print, rrr, profile = ut.inject2(__name__)

# from pysseg import getLogger
# logger = getLogger(__name__)
# print = logger.info


def testdata_siam_desc(num_data=128, desc_dim=8):
    rng = np.random.RandomState(0)
    network_output = vt.normalize_rows(rng.rand(num_data, desc_dim))
    vecs1 = network_output[0::2]
    vecs2 = network_output[1::2]
    # roll vecs2 so it is essentially translated
    vecs2 = np.roll(vecs1, 1, axis=1)
    network_output[1::2] = vecs2
    # Every other pair is an imposter match
    network_output[::4, :] = vt.normalize_rows(rng.rand(32, desc_dim))
    #data_per_label = 2

    vecs1 = network_output[0::2].astype(np.float32)
    vecs2 = network_output[1::2].astype(np.float32)

    def true_dist_metric(vecs1, vecs2):
        g1_ = np.roll(vecs1, 1, axis=1)
        dist = vt.L2(g1_, vecs2)
        return dist
    #l2dist = vt.L2(vecs1, vecs2)
    true_dist = true_dist_metric(vecs1, vecs2)
    labels = (true_dist > 0).astype(np.float32)
    vecs1 = torch.from_numpy(vecs1)
    vecs2 = torch.from_numpy(vecs2)
    labels = torch.from_numpy(labels)
    return vecs1, vecs2, labels


class ContrastiveLoss(torch.nn.Module):
    """
    Contrastive loss function.

    References:
        https://github.com/delijati/pytorch-siamese/blob/master/contrastive.py

    LaTeX:
        $(y E)^2 + ((1 - y) max(m - E, 0)^2)$

    Example:
        >>> from ibeis.algo.verif.siamese import *
        >>> vecs1, vecs2, labels = testdata_siam_desc()
        >>> self = ContrastiveLoss()
        >>> ut.exec_func_src(self.forward, globals())
        >>> func = self.forward
        >>> loss2x, dist_l2 = ut.exec_func_src(self.forward, globals(), globals(), keys=['loss2x', 'dist_l2'])
        >>> ut.quit_if_noshow()
        >>> loss2x, dist_l2, labels = map(np.array, [loss, dist_l2, labels])
        >>> labels = labels.astype(np.bool)
        >>> dist0_l2 = dist_l2[labels]
        >>> dist1_l2 = dist_l2[~labels]
        >>> loss0 = loss2x[labels] / 2
        >>> loss1 = loss2x[~labels] / 2
        >>> import plottool as pt
        >>> pt.plot2(dist0_l2, loss0, 'x', color=pt.TRUE_BLUE, label='imposter_loss', y_label='loss')
        >>> pt.plot2(dist1_l2, loss1, 'x', color=pt.FALSE_RED, label='genuine_loss', y_label='loss')
        >>> pt.gca().set_xlabel('l2-dist')
        >>> pt.legend()
        >>> ut.show_if_requested()
    """

    def __init__(self, margin=1.0):
        ut.super2(ContrastiveLoss, self).__init__()
        self.margin = margin

    def forward(self, vecs1, vecs2, labels):
        # euclidian distance
        diff = vecs1 - vecs2
        dist_sq = torch.sum(torch.pow(diff, 2), 1)
        dist_l2 = torch.sqrt(dist_sq)

        loss2x_genuine  = (1 - labels) * torch.pow(torch.clamp(self.margin - dist_l2, min=0.0), 2)
        loss2x_imposter = labels * dist_sq
        loss2x = loss2x_genuine + loss2x_imposter
        ave_loss = torch.sum(loss2x) / 2.0 / vecs1.size()[0]
        return ave_loss


class NetMathParams(object):

    @classmethod
    def lookup(cls, key_or_scheduler):
        """
        Accepts either a string that encodes a known scheduler or a
        custom callable that is returned as-is.

        Args:
            key_or_scheduler (str or func): scheduler name or the func itself
        """
        if isinstance(key_or_scheduler, six.string_types):
            key = key_or_scheduler
            scheduler = getattr(cls, key)
        else:
            scheduler = key_or_scheduler
        return scheduler


class LRSchedules(NetMathParams):
    """
    A collection of standard and custom learning rate schedulers
    """

    @staticmethod
    def exp(optimizer, epoch, init_lr=0.001, lr_decay_epoch=2):
        """Decay learning rate by a factor of 0.1 every lr_decay_epoch epochs."""
        lr = init_lr
        # epoch += 1
        if epoch % lr_decay_epoch == 0 and epoch is not 0:
            lr *= 0.1

        if epoch % lr_decay_epoch == 0:
            print('LR is set to {}'.format(lr))

        for param_group in optimizer.param_groups:
            param_group['lr'] = lr

        return lr


class Criterions(NetMathParams):
    """
    A collection of standard and custom loss criterion
    """

    @staticmethod
    def cross_entropy2d(output, label, weight=None, size_average=True):
        """
        https://github.com/ycszen/pytorch-seg/blob/master/loss.py
        """
        n, c, h, w = output.size()

        log_p = torch.nn.functional.log_softmax(output, dim=1)
        log_p = log_p.transpose(1, 2).transpose(2, 3).contiguous()

        # TODO: ignore any negative label
        # for ignore in ignore_labels:
        #     label[label == ignore] = -1

        # Flatten Predictions
        log_p = log_p[label.view(n, h, w, 1).repeat(1, 1, 1, c) >= 0].view(-1, c)

        # Flatten Labels
        target_mask = label >= 0
        target = label[target_mask]

        # from pysseg import metrics
        # confusion_matrix()
        # loss = torch.nn.functional.nll_loss(log_p, target, weight=weight, size_average=False)
        loss = torch.nn.functional.cross_entropy(log_p, target, weight=weight, size_average=False)
        if size_average:
            loss /= target_mask.data.sum()
        return loss

    ContrastiveLoss = ContrastiveLoss


class Optimizers(NetMathParams):
    Adam = torch.optim.Adam
    SGD = torch.optim.SGD


class Metrics(NetMathParams):

    def tpr(outputs, label):
        """ true positive rate """
        pred = outputs.data.max(dim=1)[1].cpu().numpy()
        true = label.data.cpu().numpy()

        is_tp = pred == true
        tpr = is_tp.sum() / is_tp.size
        return tpr
