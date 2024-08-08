from writeconfig import *
from pathlib import Path
from argparse import ArgumentParser, FileType
import json

parser = ArgumentParser(description="Construct config csv for a fast-likelihood trial")
parser.add_argument('config_file_out', type=Path)
parser.add_argument('meta_params', type=FileType("r"))
args = parser.parse_args()

with args.meta_params as params_file:
    params = json.load(params_file)

likelihood_methods = params['likelihood_methods']
bin_widths = params['bin_widths']
mesh_spacings = params['mesh_spacings']
estimator_methods =  params['estimator_methods']
dets = params['detectors']

output_dir = Path("$OUT_DIR")
img_type = "$SAVE_IMG_TYPE"

img_outdir = output_dir / 'imgs'
json_outdir = output_dir / 'jsons'

def cartesian_product(a: list, b: list, asymmetric: bool = False):
    pairs = []
    for i, a_item in enumerate(a):
        for j, b_item in enumerate(b):
            if (i < j or not asymmetric):
                pairs.append((a_item, b_item))
    return pairs

det_pairs = cartesian_product(dets, dets, True)

with LineWriter.from_path(args.config_file_out) as w:
    w.module("Control", "Pass", line=1)
    w.newline()
    w.comment("Accelerated Likelihood Calculation with background")
    w.newline()
    
    w.module("SN", "Write",
        on=['alert','report'],
        write= tuple_pairs(
            {
                "truth/sn_spec/time": "$SN_TIME",
                "truth/model": "'$MODEL'", "truth/species": "'$SPECIES'",
                "fpatterns/trial_json": q(json_outdir / "trials" / "{}-{}-{}.json"),
                "fpatterns/report_json": q(json_outdir / "reports" / "{}-{}-{}.json"),
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

    for det1, det2 in det_pairs:
        w.newline()

        pairkey = f"{det1}-{det2}"
        pair_field = ('det_pairs', pairkey)

        true_t1_field = ('truth', 'dets', det1, 'true_t')
        true_t2_field = ('truth', 'dets', det2, 'true_t')

        binnings_field = (*pair_field, 'binnings')
        for bin_width in bin_widths:
            binning_field = (*binnings_field, bin_width)
            binning_name_suffix = f"{bin_width}s-bin_{pairkey}"

            w.module(binning_name_suffix, "fastlike.SeriesBinning", 
                in_series1_field=('timeseries', det1), in_series2_field=('timeseries',det2),
                out_field=binning_field,
                bin_width=bin_width, window="$WINDOW",
                det1_bg=f"$BG_{det1}", det2_bg=f"$BG_{det2}"
            )

            meshes_field = (*binning_field, 'meshes')
            for mesh_spacing in mesh_spacings:
                mesh_field = (*meshes_field, mesh_spacing)
                lag_mesh_field = (*mesh_field, 'lag_mesh')

                mesh_name_suffix = f"{mesh_spacing}s-mesh_{binning_name_suffix}"

                w.module(mesh_name_suffix, "fastlike.SeriesBinningMesh",
                    in_field=binning_field, out_field=mesh_field,
                    mesh_spacing=mesh_spacing
                )

                likelihoods_field = (*mesh_field, 'likelihood_methods')

                for like_method_name, like_plugin_class, like_kwargs in likelihood_methods:
                    like_method_field = (*likelihoods_field, like_method_name)
                    like_method_name_suffix = f"{like_method_name}_{mesh_name_suffix}"
                    like_mesh_field = (*like_method_field, 'likelihood_mesh')

                    w.newline()
                    w.module(f"likemesh-{like_method_name_suffix}", like_plugin_class,
                        in_binning_field = binning_field, in_mesh_field = mesh_field,
                        out_field = like_mesh_field,
                        **like_kwargs
                    )

                    est_methods_field = (*like_method_field, 'estimators')

                    like_method_img_outdir = img_outdir / pairkey / like_method_name / f"bw-{bin_width}s" / f"mesh-{mesh_spacing}s"

                    for est_method_name, est_plugin_class, est_kwargs in estimator_methods:
                        est_method_field = (*est_methods_field, est_method_name)
                        est_method_name_suffix = f"{est_method_name}_{like_method_name_suffix}"

                        out_stats_field = (*pair_field, 'method_summaries', like_method_name, est_method_name, bin_width, mesh_spacing)
                        
                        def pull_img_pattern(pullname):
                            return q(like_method_img_outdir / "report" / f"{est_method_name}-{pullname}-{{1}}-{{2}}.{img_type}")

                        w.newline()
                        w.module(f"lag_{est_method_name_suffix}", est_plugin_class,
                            in_lags_field = lag_mesh_field,
                            in_likelihoods_field = like_mesh_field,
                            out_field = est_method_field,
                            **est_kwargs
                        )

                        w.module(f"pull-score_{est_method_name_suffix}", "LagPull",
                            out_field=(*est_method_field, 'pull_score'),
                            out_diff_field=(*est_method_field, 'raw_error'),
                            in_obs_field=(*est_method_field, 'dt'),
                            in_err_field=(*est_method_field, 'dt_err'),
                            in_true_field=true_t1_field,
                            in_base_field=true_t2_field
                        )

                        w.module(f"pull-acc_{est_method_name_suffix}", "Accumulator",
                            title=f"'Pull Scores'",
                            in_field=(*est_method_field, 'pull_score'),
                            out_field=(*est_method_field, 'pull_scores'),
                            alert_pass=True, clear_on=[], override=False,
                        )

                        w.module(f"pull-plot_{est_method_name_suffix}", "renderers.fastlike.PairPullPlot",
                            in_pull_field = (*est_method_field, 'pull_scores'),
                            out_stats_field = (*out_stats_field, 'pull_score'),
                            filename = pull_img_pattern("pull-scores"), 
                        )

                        w.module(f"err-acc_{est_method_name_suffix}", "Accumulator",
                            title=f"'Errors'",
                            in_field=(*est_method_field, 'raw_error'),
                            out_field=(*est_method_field, 'raw_errors'),
                            alert_pass=True, clear_on=[], override=False,
                        )

                        w.module(f"err-plot_{est_method_name_suffix}", "renderers.fastlike.PairPullPlot",
                            title="'Error Distribution'",
                            in_pull_field = (*est_method_field, 'raw_errors'),
                            out_stats_field = (*out_stats_field, 'raw_error'),
                            filename = pull_img_pattern("errors"),
                        )

                    w.module(f"plot-like+diffs_{like_method_name_suffix}", "renderers.fastlike.PairTrialPlot",
                        in_lag_mesh_field = lag_mesh_field,
                        in_like_mesh_field = like_mesh_field,
                        in_ests_field = est_methods_field,
                        in_true_t1_field = true_t1_field,
                        in_true_t2_field = true_t2_field,
                        max_plots = "$MAX_PLOTS",
                        ncolours = len(estimator_methods),
                        filename = q(like_method_img_outdir / "trials"  / f"lag-estimates-{{1}}-{{2}}.{img_type}"), 
                    )

        for like_method_name, like_plugin_class, like_kwargs in likelihood_methods:
            for est_method_name, est_plugin_class, est_kwargs in estimator_methods:
                in_stats_field = (*pair_field, 'method_summaries', like_method_name, est_method_name)
                pair_method_name_suffix = f"{est_method_name}_{like_method_name}_{pairkey}"

                # w.module(f"score-compare_{pair_method_name_suffix}", )

    save_fields = ['coincident_detectors', 'truth', 'det_pairs']

    w.newline(2)
    w.module("TrialInfo", "renderers.JsonOutput", on=['alert'], fields=save_fields, filename=q(output_dir / "jsons" / "trials" / "{}-{}-{}.json"), suppress_unjsonable=True)
    w.module("PullInfo", "renderers.JsonOutput",
        on=['report'], fields=save_fields, filename=q(output_dir / "jsons" / "report-{}-{}-{}.json"),
        suppress_unjsonable=True, json_kwargs={ "indent": 2 }
    )
    w.module("PullPickle", "renderers.PickleOutput", on=['report'], filename=q(output_dir / "jar" / "{}-{}-{}.pkl"))