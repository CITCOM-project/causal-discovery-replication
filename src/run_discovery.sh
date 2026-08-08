for system in "carla" "causal_test_adequacy" "causal_testing_framework"
do
    for data_file in $(find "data/${system}" -type f -name "*.csv")
    do
        root=$(dirname ${data_file})
        ground_truth="$root/truth.dot"
        for seed in {1..30}
        do
            for data in 0.2 0.4 0.6 0.7 0.8 1
            do
                for technique in "NSGADiscovery" "HillClimberDiscovery" "HillClimbSearch" "PC" "GES"
                do
                    python src/discovery.py -d ${data_file} -o "results/${root}/technique-${technique}/knowledge-0/data-${data}/seed-${seed}.dot" -t ${technique} -D ${data} -r ${ground_truth}
                    if [ "$technique" != "GES" ]; then # Skip for GES as expert knowledge isn't supported
                        for knowledge in 0.2 0.4 0.6 0.8
                        do
                            python src/discovery.py -d ${data_file} -o "results/$root/technique-${technique}/knowledge-${knowledge}/data-${data}/seed-${seed}.dot" -t ${technique} -r ${ground_truth} -e ${knowledge} -D ${data}
                        done
                    fi
                done
            done
        done
    done
done
