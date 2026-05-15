#!/bin/bash
#PBS -N o
#PBS -l nodes=1:ppn=16:gpus=1
#PBS -l mem=88G
#PBS -l walltime=48:00:00
#PBS -j oe
cd $PBS_O_WORKDIR

ulimit -s unlimited
ulimit -l unlimited

export CUDA_VISIBLE_DEVICES=2

module purge
module load gcc/11.3.0 #
module load cuda/12.2

export PATH=/usr/local/cuda/bin:/opt/plumed/2.9.0-gcc11.3.0/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:/opt/gsl/2.7-gcc11.3.0/lib:/opt/plumed/2.9.0-gcc11.3.0/lib:$LD_LIBRARY_PATH
export PLUMED_KERNEL=/opt/plumed/2.9.0-gcc11.3.0/lib/libplumedKernel.so

GPUMD_BIN=/home/marunlin/opt/gpumd/GPUMD-4.7/src/build1/gpumd

"$GPUMD_BIN" > gpumd.out 2>&1
