N=10
(
    for data in 100 #1000 5000
    do
        for technique in "HillClimbSearch" "PC" "GES" #"HillClimberDiscovery"
        do
            for nodes in 10 #20 30
            do
                for p_edge in 0.25 #0.5 0.75 1
                do
                    for p_conditional in 0.25 #0.5 0.75 1
                    do
                        for seed in {1..30}
                        do
                            ((i=i%N)); ((i++==0)) && wait
                            output_file="results_synthetic/technique-${technique}/knowledge-0/data-${data}/seed-${seed}.dot"
                            if [ ! -f "$output_file" ]; then
                                python src/synthetic_discovery.py -o ${output_file} -t ${technique} -D ${data} -n ${nodes} -E ${p_edge} -c ${p_conditional} -s ${seed} &
                            fi
                            if [ "$technique" != "GES" ]; then # Skip for GES as expert knowledge isn't supported
                                for knowledge in 0.2 0.4 0.6 0.8
                                do
                                    output_file="results_synthetic/technique-${technique}/knowledge-${knowledge}/data-${data}/seed-${seed}.dot"
                                    if [ ! -f "$output_file" ]; then
                                        python src/synthetic_discovery.py -o ${output_file} -t ${technique} -D ${data} -n ${nodes} -E ${p_edge} -c ${p_conditional} -k ${knowledge} -s ${seed} &
                                    fi
                                done
                            fi
                        done
                    done
                done
            done
        done
    done
)
