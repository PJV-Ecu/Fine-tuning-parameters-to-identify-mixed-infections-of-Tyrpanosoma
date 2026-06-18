#!/bin/bash

# Define reference and output
REFERENCE_FASTA="Trypanosoma_alignment_17_nogaps.fas"
minimap2 -k 19 -d ref.mmi ${REFERENCE_FASTA}
mkdir -p results

# Set threshold for Mapping Quality (30 is roughly 99.9% confidence)
MAPQ_THRESH=10

for fastq_in in fastq_cleaned/*.fastq; do
    base=$(basename ${fastq_in} .fastq)
    echo "Processing ${base}..."
    
    # CHANGED: -ax to -cx (Output PAF format with CIGAR)
    minimap2 -cx map-ont -s 60 -B 4 ref.mmi ${fastq_in} 2> /dev/null | \
    awk -v mapq_thresh="$MAPQ_THRESH" '
    {
        # PAF Standard Columns: 
        # $1=QueryName, $2=QueryLen, $3=QueryStart, $4=QueryEnd, $5=Strand
        # $6=TargetName, $7=TargetLen, $8=TargetStart, $9=TargetEnd
        # $10=Matches, $11=BlockLen, $12=MapQ

        # Ensure valid line
        if ($2 > 0 && $11 > 0) {
        
            # --- METRICS CALCULATIONS ---
            
            # 1. Query Coverage (How much of the READ is used)
            q_cov = ($4 - $3) / $2;
            
            # 2. Target Coverage (How much of the REFERENCE GENE is covered)
            t_cov = ($9 - $8) / $7;
            
            # 3. Identity (Matches / Alignment Block Length)
            ident = $10 / $11;

            # --- FILTERING ---
            
            # Filter 1: Robustness Check (Mapping Quality)
            # This ensures the read maps UNIQUELEY to this species and not another
            if ($12 >= mapq_thresh) {
            
                # Filter 2: Biological Check (Identity & Coverage)
                # Logic: High identity AND (good read coverage OR good reference coverage)
                if ((q_cov >= 0.90 || t_cov >= 0.90) && ident >= 0.95) {
                    print $0;
                }
            }
        }
    }' > results/${base}.filtered.paf

    # Count hits
    if [ -s results/${base}.filtered.paf ]; then
        # Column 6 is TargetName in PAF
        cut -f 6 results/${base}.filtered.paf | sort | uniq -c | \
        awk '{print $2 "\t" $1}' > results/${base}.counts.txt
        echo "Done. Results saved to results/${base}.counts.txt"
    else
        echo "Warning: No reads passed the filters for ${base}."
    fi
done