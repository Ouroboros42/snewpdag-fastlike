from writeconfig import LineWriter, tuple_pairs

import argparse

root = "/home/jesu4059/snewpdag-fastlike/"
outroot = "/data/snoplus/lucas/snout/"

defined_detectors = ['IC', 'JUNO', 'SK', 'LVD', 'SNOP']

parser = argparse.ArgumentParser(description="Construct config csv for a fast-likelihood trial")
parser.add_argument('outfile', type=argparse.FileType('w'))
parser.add_argument('detectors', nargs='+', choices=defined_detectors)
args = parser.parse_args()

dets = args.detectors
output_dir = outroot + f"fastlike/{'-'.join(dets)}/$NOW/"

det_pairs = []
for i, det1 in enumerate(dets):
    for det2 in dets[i+1:]:
        det_pairs.append((det1, det2))

with args.outfile as outfile:
    w = LineWriter(outfile)

    w.module("Control", "Pass", line=1)
    w.newline()
    w.comment("Accelerated Likelihood Calculation with background")
    w.newline()
    
    w.module("SN","Write",
        on=['alert','report'],
        write= tuple_pairs(
            { "truth/sn_spec/time": "$SN_TIME" },
            { "estimator/event_hist/nbins": "$NBINS", "estimator/event_hist/twindow": "$WINDOW" },
            { "estimator/likelihood_mesh/npoints": "$NLAGMESH" },
            { "truth/model": "'$MODEL'", "truth/species": "'$SPECIES'" },
            { f"truth/dets/{det}/yield": f"$YIELD_{det}" for det in dets },
            { f"truth/dets/{det}/background": f"$BG_{det}" for det in dets },
            png_pattern=f"'{output_dir}imgs/{{}}-{{}}-{{}}.png'",
            pickle_pattern=f"'{output_dir}jar/{{}}-{{}}-{{}}.pickle'",
            json_pattern=f"'{output_dir}jsons/{{}}-{{}}-{{}}.json'",
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
        detector_location=f"'{root}snewpdag/data/detector_location.csv'",
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
            sig_filetype="'tng'",
            sig_filename="'/home/tseng/dev/snews/numodels/ls220-$MODEL/neutrino_signal_$SPECIES-LS220-$MODEL.data'"
        )
        w.module(f"{det}-bg", "gen.Uniform",
            field=('timeseries',det),
            rate=f"$BG_{det}",
            tmin="$SN_SAMPLE_START", tmax="$SN_SAMPLE_STOP"
        )

    w.newline()
    for det1, det2 in det_pairs:
        pairkey = f"{det1}-{det2}"

        w.module(f"diff-{pairkey}", "LikeLag",
            in_series1_field=('timeseries', det1), in_series2_field=('timeseries',det2),
            out_field="'dts'", out_key=f"'{pairkey}'",
            det1_bg=f"$BG_{det1}", det2_bg=f"$BG_{det2}",
            tnbins="$NBINS", twidth="$WINDOW", nlags="$NLAGMESH"
        )

        w.module(f"pull-score-{pairkey}", "LagPull",
            out_field=('dts',pairkey,'pull_score'),
            in_obs_field=('dts',pairkey,'dt'),
            in_err_field=('dts',pairkey,'dt_err'),
            in_true_field=('truth','dets',det1,'true_t'),
            in_base_field=('truth','dets',det2,'true_t')
        )

        w.module(f"pull-acc-{pairkey}", "Accumulator",
            title=f"'pull_scores_{det1}_{det2}'",
            in_field=('dts',pairkey,'pull_score'),
            out_field=('analysis','pulls',pairkey),
            alert_pass=True, clear_on=[]
        )
        
        w.module(f"opt-pull-score-{pairkey}", "LagPull",
            out_field=('dts',pairkey,'opt_pull_score'),
            in_obs_field=('dts',pairkey,'opt_dt'),
            in_err_field=('dts',pairkey,'dt_err'),
            in_true_field=('truth','dets',det1,'true_t'),
            in_base_field=('truth','dets',det2,'true_t')
        )

        w.module(f"opt-pull-acc-{pairkey}", "Accumulator",
            title=f"'opt_pull_scores_{pairkey}'",
            in_field=('dts',pairkey,'opt_pull_score'),
            out_field=('analysis','opt_pulls',pairkey),
            alert_pass=True, clear_on=[]
        )

        w.module(f"plot-diff-{pairkey}", "renderers.fastlike.PairTrialPlot",
            in_dt_field = ('dts',pairkey),
            in_true_t1_field = ('truth','dets',det1,'true_t'),
            in_true_t2_field = ('truth','dets',det2,'true_t'),
            filename = "'[png_pattern]'", 
        )

        w.module(f"fit-pull-plot-{pairkey}", "renderers.fastlike.PairPullPlot",
            in_pull_field = ('analysis', 'pulls', pairkey),
            filename = "'[png_pattern]'", 
        )

        w.module(f"opt-pull-plot-{pairkey}", "renderers.fastlike.PairPullPlot",
            in_pull_field = ('analysis', 'opt_pulls', pairkey),
            filename = "'[png_pattern]'", 
        )

    w.newline()
    
    # w.module("FullPickle", "renderers.PickleOutput", filename="'[pickle_pattern]'")

    global_info = ['coincident_detectors', 'estimator', 'truth']
    trial_info = global_info + ['dts']
    pull_info = global_info + ['analysis']

    w.module("TrialInfo", "renderers.JsonOutput", filename="'[json_pattern]'", on=['alert'], fields=trial_info)
    w.module("PullInfo", "renderers.JsonOutput", filename="'[json_pattern]'", on=['report'], fields=pull_info)