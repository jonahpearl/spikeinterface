import numpy as np

from .basepreprocessor import BasePreprocessor, BasePreprocessorSegment
from spikeinterface.core.core_tools import define_function_from_class
from spikeinterface.preprocessing import preprocessing_tools
import scipy.stats

class InterpolateBadChannels(BasePreprocessor):
    """
    Interpolate the channel labeled as bad channels using linear interpolation.
    This is based on the distance (Gaussian kernel) from the bad channel,
    as determined from x,y channel coordinates.

    Details of the interpolation function (Olivier Winter) used in the IBL pipeline
    can be found at:

    International Brain Laboratory et al. (2022). Spike sorting pipeline for the
    International Brain Laboratory. https://www.internationalbrainlab.com/repro-ephys

    Parameters
    ----------

    bad_channel_indexes : numpy array, indexes of the bad channels to interpolate.

    sigma_um : distance between sequential channels in um. If None, will use
               the most common distance between y-axis channels.

    p : exponent of the Gaussian kernel. Determines rate of decay
        for distance weightings.

    """
    name = 'interpolate_bad_channels'

    def __init__(self, recording, bad_channel_indexes, sigma_um=None, p=1.3, ):
        BasePreprocessor.__init__(self, recording)

        self.check_inputs(recording, bad_channel_indexes)

        self.bad_channel_indexes = bad_channel_indexes
        contact_positions = recording.get_probe().contact_positions

        if sigma_um is None:
            sigma_um = self.get_recommended_sigma_um(recording, contact_positions)

        weights = self.calculate_weights_and_lock_channel_idxs(contact_positions,
                                                               sigma_um,
                                                               p)

        for parent_segment in recording._recording_segments:
            rec_segment = InterpolateBadChannelsSegment(parent_segment,
                                                        bad_channel_indexes,
                                                        weights)
            self.add_recording_segment(rec_segment)

        self._kwargs = dict(recording=recording.to_dict(),
                            bad_channel_indexes=bad_channel_indexes,
                            p=p,
                            sigma_um=sigma_um)

    def get_recommended_sigma_um(self, recording, contact_positions):
        """
        Get the most common distance between channels on the y-axis
        """
        y = contact_positions[:, 1]

        return scipy.stats.mode(np.diff(np.unique(y)), keepdims=False)[0]

    def calculate_weights_and_lock_channel_idxs(self, contact_positions, sigma_um, p):
        """
        Pre-compute the channel weights for this InterpolateBadChannels
        instance.
        """
        weights = preprocessing_tools.get_kriging_bad_channel_weights(contact_positions,
                                                                      self.bad_channel_indexes,
                                                                      sigma_um,
                                                                      p)

        self.bad_channel_indexes.setflags(write=False)

        return weights

    def check_inputs(self, recording, bad_channel_indexes):

        if type(bad_channel_indexes) != np.ndarray:
            raise TypeError("Bad channel indexes must be a numpy array.")

        if recording.get_property('contact_vector') is None:
            raise ValueError('A probe must be attached to use bad channel interpolation. Use set_probe(...)')

        if recording.get_probe().si_units != "um":
            raise NotImplementedError("Channel spacing units must be um")


class InterpolateBadChannelsSegment(BasePreprocessorSegment):

    def __init__(self, parent_recording_segment, bad_channel_indexes, weights):
        BasePreprocessorSegment.__init__(self, parent_recording_segment)

        self._bad_channel_indexes = bad_channel_indexes
        self._weights = weights

    def get_traces(self, start_frame, end_frame, channel_indices):

        traces = self.parent_recording_segment.get_traces(start_frame,
                                                          end_frame,
                                                          slice(None))

        traces = traces.copy()

        traces[:, self._bad_channel_indexes] = traces @ self._weights

        return traces

interpolate_bad_channels = define_function_from_class(source_class=InterpolateBadChannels, name='interpolate_bad_channels')
