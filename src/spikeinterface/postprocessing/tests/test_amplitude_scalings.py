import numpy as np
import pytest

from spikeinterface.postprocessing.tests.common_extension_tests import AnalyzerExtensionCommonTestSuite

from spikeinterface.postprocessing import ComputeAmplitudeScalings


class TestAmplitudeScalingsExtension(AnalyzerExtensionCommonTestSuite):

    @pytest.mark.parametrize("params", [dict(handle_collisions=True), dict(handle_collisions=False)])
    def test_extension(self, params):
        self.run_extension_tests(ComputeAmplitudeScalings, params)

    def test_scaling_values(self):
        sorting_analyzer = self._prepare_sorting_analyzer("memory", True, ComputeAmplitudeScalings)
        sorting_analyzer.compute("amplitude_scalings", handle_collisions=False)

        spikes = sorting_analyzer.sorting.to_spike_vector()

        ext = sorting_analyzer.get_extension("amplitude_scalings")

        for unit_index, unit_id in enumerate(sorting_analyzer.unit_ids):
            mask = spikes["unit_index"] == unit_index
            scalings = ext.data["amplitude_scalings"][mask]
            median_scaling = np.median(scalings)
            np.testing.assert_array_equal(np.round(median_scaling), 1)

        # import matplotlib.pyplot as plt
        # fig, ax = plt.subplots()
        # ax.hist(ext.data["amplitude_scalings"])
        # plt.show()
