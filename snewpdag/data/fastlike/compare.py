from writeconfig import *
from pathlib import Path
from argparse import ArgumentParser, FileType

defined_detectors = ['IC', 'JUNO', 'SK', 'LVD', 'SNOP']

parser = ArgumentParser(description="Construct config csv for a fast-likelihood trial")
parser.add_argument('config_file_out', type=Path)
parser.add_argument('detectors', nargs='+', choices=defined_detectors)
args = parser.parse_args()

dets = args.detectors

output_dir = Path("$OUT_DIR")

det_pairs = []
for i, det1 in enumerate(dets):
    for det2 in dets[i+1:]:
        det_pairs.append((det1, det2))

with LineWriter.from_path(args.config_file_out) as w:
    w.module("Control", "Pass", line=1)
    w.newline()
    w.comment("Accelerated Likelihood Calculation with background")
    w.newline()
    
    w.module("SN","Write",
        on=['alert','report'],
        write= tuple_pairs(
            {
                "truth/sn_spec/time": "$SN_TIME",
                "estimator/event_hist/bin_width": "$BIN_WIDTH", "estimator/event_hist/window": "$WINDOW",
                "estimator/polyfit/mesh_spacing": "$LAG_MESH_STEP",
                "truth/model": "'$MODEL'", "truth/species": "'$SPECIES'",
                "fpatterns/trial_png": q(output_dir / "imgs" / "trials" / "{}-{}-{}.png"),
                "fpatterns/trial_json": q(output_dir / "jsons" / "trials" / "{}-{}-{}.json"),
                "fpatterns/report_png": q(output_dir / "imgs" / "reports" / "{}-{}-{}.png"),
                "fpatterns/report_json": q(output_dir / "jsons" / "reports" / "{}-{}-{}.json"),
            },
            { f"truth/dets/{det}/yield": f"$YIELD_{det}" for det in dets },
            { f"truth/dets/{det}/background": f"$BG_{det}" for det in dets },
            coincident_detectors=dets,
        )
    )

    w.newline()
    w.comment("This is the simplest way to randomly generate isotropic vectors. Magnitude is unimportant", True)
    w.module("SN-Direction", "gen.RandomParameter",
        out_field="'truth/sn_spec/direction_vec'",
        dist_spec={ "type": "normal", "size": 3 }
    )
    
    w.module("SN-times", "gen.DynamicTrueTimes",
        detector_location="'$DETECTOR_LOCATIONS'",
        detectors=dets,
        sn_spec_field="'truth/sn_spec'",
    )

    for det in dets:
        w.newline()
        w.module(f"{det}-new","ops.NewTimeSeries",
            out_field=('timeseries',det),
            start="$SN_SAMPLE_START", stop="$SN_SAMPLE_STOP"
        )
        w.module(f"{det}-signal","gen.GenTimeDist",
            field=('timeseries',det),
            sig_mean=f"$YIELD_{det}", sig_t0=('truth','dets',det,'true_t'),
            sig_filetype="$SIGNAL_FILETYPE",
            sig_filename="'$SIGNAL_FILE'"
        )
        w.module(f"{det}-bg", "gen.Uniform",
            field=('timeseries',det),
            rate=f"$BG_{det}",
            tmin="$SN_SAMPLE_START", tmax="$SN_SAMPLE_STOP"
        )

    w.newline()
    for det1, det2 in det_pairs:
        pairkey = f"{det1}-{det2}"
        pair_field = ('det_pairs', pairkey)
        binning_field = (*pair_field, 'binning')

        w.module(f"bin-{pairkey}", "fastlike.HistCompare", 
            in_series1_field=('timeseries', det1), in_series2_field=('timeseries',det2),
            out_field=binning_field,
            bin_width="$BIN_WIDTH", window="$WINDOW",
            det1_bg=f"$BG_{det1}", det2_bg=f"$BG_{det2}"
        )

        methods_field = (*pair_field, 'lag_methods')

        true_t1_field = ('truth', 'dets', det1, 'true_t')
        true_t2_field = ('truth', 'dets', det2, 'true_t')

        for method_name, plugin_class, kwargs in (
            ("anneal", "fastlike.AnnealLag", { "mesh_spacing": "$LAG_MESH_STEP" }),
            ("polyfit", "fastlike.PolyFitLag", { "mesh_spacing": "$LAG_MESH_STEP" }),
        ):
            method_field = (*methods_field, method_name)

            w.module(f"lag-{method_name}-{pairkey}", plugin_class, in_field = binning_field, out_field = method_field, **kwargs)

            w.module(f"pull-score-{method_name}-{pairkey}", "LagPull",
                out_field=(*method_field, 'pull_score'),
                out_diff_field=(*method_field, 'raw_error'),
                in_obs_field=(*method_field, 'dt'),
                in_err_field=(*method_field, 'dt_err'),
                in_true_field=true_t1_field,
                in_base_field=true_t2_field
            )

            w.module(f"pull-acc-{method_name}-{pairkey}", "Accumulator",
                title=f"'Pull Scores for {method_name}: {det1}-{det2}'",
                in_field=(*method_field, 'pull_score'),
                out_field=(*method_field, 'pull_scores'),
                alert_pass=True, clear_on=[]
            )
            w.module(f"pull-plot-{method_name}-{pairkey}", "renderers.fastlike.PairPullPlot",
                in_pull_field = (*method_field, 'pull_scores'),
                filename = "'[fpatterns/report_png]'", 
            )

            w.module(f"err-acc-{method_name}-{pairkey}", "Accumulator",
                title=f"'Errors for {method_name}: {det1}-{det2}'",
                in_field=(*method_field, 'raw_error'),
                out_field=(*method_field, 'raw_errors'),
                alert_pass=True, clear_on=[]
            )
            w.module(f"err-plot-{method_name}-{pairkey}", "renderers.fastlike.PairPullPlot",
                title="'Error Distribution'",
                in_pull_field = (*method_field, 'raw_errors'),
                filename = "'[fpatterns/report_png]'", 
            )

        w.module(f"plot-diffs-{pairkey}", "renderers.fastlike.PairTrialPlot",
            in_dt_field = methods_field,
            in_true_t1_field = true_t1_field,
            in_true_t2_field = true_t2_field,
            filename = "'[fpatterns/trial_png]'", 
        )

        w.newline()

    global_info = ['coincident_detectors', 'estimator', 'truth']
    trial_info = global_info + ['det_pairs']
    pull_info = global_info + ['analysis']

    w.module("TrialInfo", "renderers.JsonOutput", on=['alert'], fields=trial_info, filename="'[fpatterns/trial_json]'", suppress_unjsonable=True)
    w.module("PullInfo", "renderers.JsonOutput", on=['report'], fields=pull_info, filename="'[fpatterns/report_json]'", suppress_unjsonable=True)