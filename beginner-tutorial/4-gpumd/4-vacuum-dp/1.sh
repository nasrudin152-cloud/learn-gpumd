source /opt/modules/module.sh
module load deepmd/2.2.4 nccl/2.18.5_cuda11 lammps/2Aug2023_update1
export OMP_NUM_THREADS=4
export TF_INTRA_OP_PARALLELISM_THREADS=4
export TF_INTER_OP_PARALLELISM_THREADS=4
module load cuda

export DP_INTERFACE_PREC=low


export CUDA_VISIBLE_DEVICES=2
#mpirun -np 16 lmp_mpi -in input.lammps

nohup lmp_mpi -in input.lammps > 2.log &
