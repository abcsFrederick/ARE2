#!/bin/bash
#SBATCH --partition=gpuib
#SBATCH --job-name=Aperio_Extract_Line_ROI
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=16gb
#SBATCH --output=/mnt/hpc/webdata/server/fr-s-ivg-histomics/ARE2/logs/slurm-%x.%j.out
#SBATCH --error=/mnt/hpc/webdata/server/fr-s-ivg-histomics/ARE2/logs/slurm-%x.%j.err

# $1 ROI_Index_File
# $2 Output_Folder
# $3 Prefix
# $4 Postfix
# $5 SVS_Path
# $6 Report_File
# $7 ImageID
# $8 workFolder
python3 $PWD/Aperio_Extract_Line_ROI $1 $2 $3 $4 $5 $6 $7 >> $PWD/$8