#!/usr/bin/env python

import os
from . import utils
import pysam
import subprocess
from . import consensus_sequence
from datetime import datetime
from . import variant
from . import assign_gRNA
import configparser
import sys


def run(config, threads):
	time_start = datetime.now()
	print('gRNA mutation profiling:', str(time_start),'\n')

	try:
		config_file = config
		(samtools, twoBitToFa, featureCounts) = utils.get_tools_config(config_file)
		(gRNA_bam_file, barcode, output_dir, n_consensus_reads_min, min_umi, auto, pool, ref_fasta, structure_gtf, is_10x, cb_tag, umi_tag, gene_tag) = utils.get_gRNA_mutation_config(config_file)
	except configparser.NoSectionError:
		print("No configuration file found under current folder. See documentation.")
		sys.exit(2)

	print("Output folder: " + str(output_dir))
	######## Filtering of mapped reads ########
	utils.gRNA_bam_filter(gRNA_bam_file, samtools, output_dir, threads) # time consuming
	print('Prepare bam file. Cost time: ' + str(datetime.now() - time_start) + '\n' )

	######## gRNA consensus sequence ##########
	print('Generating consensus sequence for gRNA library\n')
	bam_in_file = output_dir + 'gRNA.sorted.mapped.removedSecondaryAlignment.onlyMappedToGrnaChrom.bam'
	consensus_sequence.generate_consensus_sequence_gRNA(bam_in_file, barcode, output_dir, n_consensus_reads_min, is_10x, cb_tag, umi_tag, gene_tag)

	subprocess.call(f'{samtools} index -@ {threads} {output_dir}/consensus.bam', shell=True)

	####### Identification of mutations in the gRNA consensus ########
	variant.call_gRNA_variant(output_dir, output_dir + 'consensus.sequence.gRNA.txt', ref_fasta, structure_gtf, is_10x, cb_tag, umi_tag, gene_tag)

	####### Assign gRNAs to cells ###########
	assign_gRNA.assign_gRNA_to_cell(in_file = output_dir + 'consensus.sequence.gRNA.variant.txt', min_umi = min_umi, output_dir = output_dir, auto = auto, pool = pool)

	assign_gRNA.add_variant_type(in_file1 = output_dir + 'consensus.sequence.gRNA.variant.txt', in_file2 = output_dir + 'cells.gRNA.single.txt', in_file3 = output_dir + 'cells.gRNA.txt', structure_gtf = structure_gtf, output_dir = output_dir)

	print('gRNA mutation finished! Cost time: ' + str(datetime.now() - time_start) + '\n' )

if __name__ == '__main__':
	run()
