for seed in {1..30}
do
    for data in 100 1000 5000
    do
        for nodes in 10 20 30
        do
            for p_edge in 0.25 0.5 0.75 1
            do
                for p_conditional in 0.25 0.5 0.75 1
                do
                    for technique in "HillClimbSearch" "PC" "GES" "HillClimberDiscovery"
                    do
                        python src/synthetic_discovery.py -o "results_synthetic/technique-${technique}/knowledge-0/data-${data}/seed-${seed}.dot" -t ${technique} -D ${data} -n ${nodes} -E ${p_edge} -c ${p_conditional} -s ${seed} &
                        if [ "$technique" != "GES" ]; then # Skip for GES as expert knowledge isn't supported
                            for knowledge in 0.2 0.4 0.6 0.8
                            do
                                python src/synthetic_discovery.py -o "results_synthetic/technique-${technique}/knowledge-${knowledge}/data-${data}/seed-${seed}.dot" -t ${technique} -D ${data} -n ${nodes} -E ${p_edge} -c ${p_conditional} -k ${knowledge} -s ${seed} &
                            done
                        fi
                    done
                    wait
                done
            done
        done
    done
done
