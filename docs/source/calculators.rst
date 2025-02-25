===========
Calculators
===========

Reptar provides several driver and workers for calculations on data stored in supported file formats.
Currently, drivers for energies and gradients are provided along with workers for the following packages.

- `psi4 <https://psicode.org/psi4manual/master/index.html>`__: quantum chemical methods such as DFT and wave function methods.
    - :func:`~reptar.calculators.psi4_workers.psi4_energy`, :func:`~reptar.calculators.psi4_workers.psi4_engrad`
- `xtb-python <https://xtb-python.readthedocs.io/en/latest/>`__: a semiempirical quantum mechanics method.
    - :func:`~reptar.calculators.xtb_workers.xtb_engrad`

We use `ray <https://docs.ray.io/en/latest/ray-overview/installation.html>`__ to parallelize our calculations across one or multiple nodes.





Drivers and workers
===================

Reptar uses a driver/supervisor and worker workflow where the results are directly stored in a reptar :class:`~reptar.File`.
When running calculations, you first create a property (e.g., energy) array where all values are ``NaN``.
Each ``NaN`` value represents a calculation that still needs to run.
The driver then spawns workers with batches of calculations to run.
Once a worker is finished, we use a :class:`~reptar.Saver` object to store the results in case the job terminates early.

.. mermaid::

    flowchart LR
        start((Start)) --> props[/Property<br/>arrays/]
        props -- store --> file[(File)]
        file --> idxs[/NaN<br/>indices/]
        idxs --> driver[Driver]
        subgraph workers [Workers]
        worker1[Worker 1]
        worker2[Worker 2]
        worker3[. . .]
        end
        driver --> batchInfo[/Batch<br/>info/]
        batchInfo --> workers
        workers --> batchResults[/Batch<br/>results/]
        batchResults -- update --> file






Examples
========


Water 3-body energies with Psi4
-------------------------------

The following example walks through how to compute water 1-, 2- and 3-body energies and gradients.
We will be using the same :download:`exdir file containing a 30h2o MD simulation<./files/30h2o-md/30h2o-gfn2-md.exdir.zip>` from :ref:`this sampling tutorial <30h2o sampling tutorial>`.





Sampling water trimers
^^^^^^^^^^^^^^^^^^^^^^

First, we need to sample water trimers from the ``1-gfn2-md`` group.
Ideally we would have an even distribution of configurational space, so we first sample ``3000`` structures randomly and analyze the distribution of :func:`~reptar.descriptors.com_distance_sum`.

.. tab-set::

    .. tab-item:: Random sampling

        .. code-block:: python

            import os
            from reptar import File, Sampler
            from reptar.descriptors import Criteria, com_distance_sum

            rfile_path = './30h2o-gfn2-md.exdir'

            group_key = '/30h2o'  # The parent group.
            ref_key = f'{group_key}'  # Group to sample from.
            dest_key = f'{group_key}/samples_3h2o'  # Where to store samples.


            sample_comp_ids = ['h2o', 'h2o', 'h2o']
            quantity = 3000  # Number of trimers to sample.

            cutoff = None  # Value, list, or None. None accepts all structures.
            center_structures = True  # Translate center of mass to origin.

            # Ensures we execute from script directory (for relative paths).
            os.chdir(os.path.dirname(os.path.realpath(__file__)))

            rfile = File(rfile_path, mode='a', allow_remove=False)

            # Create the destination group if it does not exist.
            try:
                rfile.create_group(dest_key)
            except RuntimeError as e:
                if 'A directory with name' in str(e):
                    print(f'{dest_key} already exists')
                    print('Will add samples to this group')
                else:
                    raise

            criteria = Criteria(com_distance_sum, {}, cutoff=cutoff)

            sampler = Sampler(
                rfile, ref_key, rfile, dest_key, criteria=criteria,
                center_structures=center_structures
            )
            sampler.sample(sample_comp_ids, quantity)
    
    .. tab-item:: Descriptor analysis

        .. image:: ./files/30h2o-md/30h2o.3h2o-com.sum-distribution-3000.png
            :width: 400px
            :align: center

        .. code-block:: python

            import math
            import matplotlib as mpl
            import matplotlib.pyplot as plt
            import numpy as np
            import os
            from reptar import File
            from reptar.descriptors import com_distance_sum

            # Cannot be too large as bin population could not be enough.
            desc_hist_step = 0.2
            min_hist_pop = 2
            desc_plot_label = r'$\bf{Size}$ ' + '[Ang.]'

            rfile_path = '30h2o-gfn2-md.exdir'
            group_key = '/30h2o/samples_3h2o'

            fig_save_dir = './'
            fig_name = '30h2o.3h2o-com.sum-distribution'
            fig_types = ['png']
            fig_size = (3.25, 3.25)
            line_width = 1.0

            pop_color = '#908E8E'

            # Ensures we execute from script directory (for relative paths).
            os.chdir(os.path.dirname(os.path.realpath(__file__)))

            # More information: https://matplotlib.org/stable/api/matplotlib_configuration_api.html#default-values-and-styling
            font_dirs = ['./fonts/roboto']
            rc_params = {
                "figure": {"dpi": 1000},
                "font": {"family": "Roboto", "size": 8, "weight": "normal"},
                "axes": {"edgecolor": "#C2C1C1", "labelweight": "normal", "labelcolor": "#191919"},
                "xtick": {"color": "#C2C1C1", "labelcolor": "#191919", "labelsize": 7},
                "ytick": {"color": "#C2C1C1", "labelcolor": "#191919", "labelsize": 7}
            }

            # Setup matplotlib style
            font_paths = mpl.font_manager.findSystemFonts(
                fontpaths=font_dirs, fontext='ttf'
            )
            for font_path in font_paths:
                mpl.font_manager.fontManager.addfont(font_path)
            for key, params in rc_params.items():
                plt.rc(key, **params)

            rfile = File(rfile_path, mode='r')
            Z = rfile.get(f'{group_key}/atomic_numbers')
            R = rfile.get(f'{group_key}/geometry')
            entity_ids = rfile.get(f'{group_key}/entity_ids')
            desc_v = com_distance_sum(Z, R, entity_ids)

            n_R = R.shape[0]
            fig_name += f'-{n_R}'

            # Determine histogram bins.
            scale = 1.0/desc_hist_step
            desc_min = np.min(desc_v)
            desc_min_floor = math.floor(desc_min*scale)/(scale)
            desc_max = np.max(desc_v)
            desc_max_ceil = math.ceil(desc_max*scale)/(scale)
            print(f'Descriptor min: {desc_min:.3f}')
            print(f'Descriptor max: {desc_max:.3f}')

            n_bins = int(round((desc_max_ceil-desc_min_floor)/desc_hist_step, 0))
            hist_settings = {'bins': n_bins, 'range': (desc_min_floor, desc_max_ceil)}
            pop, edges = np.histogram(desc_v, **hist_settings)
            bins = 0.5 * (edges[:-1] + edges[1:])

            # Where each n-body structure goes in our size histogram
            bin_idxs = np.digitize(desc_v, edges, right=False)-1

            fig, ax = plt.subplots(1, 1 , figsize=fig_size, constrained_layout=True)

            # histogram
            ax.stairs(
                values=pop, edges=edges, fill=False, baseline=0.0, zorder=-1.0,
                edgecolor=pop_color, alpha=1.0, linewidth=line_width
            )
            ax.set_xlabel(desc_plot_label)

            ax.set_ylabel(r'$\bf{Frequency}$')

            # Axis tick label colors
            ax.tick_params(axis='y')

            for fig_type in fig_types:
                fig_path = os.path.join(fig_save_dir, fig_name + f'.{fig_type}')
                plt.savefig(fig_path)

Suppose we are primarily interested in compact trimers.
The descriptor analysis gives us a distribution where the peak is around 10.5 Angstroms with minimum and maximum values of 4.812 and 16.989.
We can tell reptar to focus on sampling structures with whose "size" is less than 7 Angstroms.
This is done by specifying ``cutoff = 7.0`` and sampling another 1000 structures.

.. image:: ./files/30h2o-md/30h2o.3h2o-com.sum-distribution-4000.png
    :width: 400px
    :align: center

Now the smallest value is 4.750.
To check to make sure we have the most compact structure, we can sample five structures with our cutoff at 4.80.

.. note::

    Reptar will continue to randomly generate structures until five are found below this aggressive cutoff.
    It is important to set the quantity to something low so that it eventually terminates and saves.

After this sampling, reptar found a compact structure with a size of 4.574 Angstroms.
We can try to find a smaller structure, but reptar could not find one after 20 minutes of random selections when the cutoff was set to 4.5.

We can also sample in a specified descriptor range.
For example, if we want structures with a size of around 12 Angstroms we can set the cutoff to ``[11.5, 12.5]``.

.. image:: ./files/30h2o-md/30h2o.3h2o-com.sum-distribution-4500.png
    :width: 400px
    :align: center

Now, we have a data set of 4500 trimers with the desired size distribution.





Sampling lower order structures
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to compute 3-body energies and gradients we also need all unique monomers and dimers.
TODO: finish this section.

.. note::

    There is no monomer descriptor analysis because :func:`~reptar.descriptors.com_distance_sum` is only valid for structures with more than one entity.

.. tab-set::

    .. tab-item:: All dimer sampling

        .. code-block:: python

            import os
            from reptar import File, Sampler
            from reptar.descriptors import Criteria, com_distance_sum

            rfile_path = './30h2o-gfn2-md.exdir'

            group_key = '/30h2o'  # The parent group.
            ref_key = f'{group_key}/samples_3h2o'  # Group to sample from.
            dest_key = f'{group_key}/samples_2h2o'  # Where to store samples.

            sample_comp_ids = ['h2o', 'h2o']
            quantity = 'all'  # Number of trimers to sample.

            cutoff = None  # Value, list, or None. None accepts all structures.
            center_structures = True  # Translate center of mass to origin.

            # Ensures we execute from script directory (for relative paths).
            os.chdir(os.path.dirname(os.path.realpath(__file__)))

            rfile = File(rfile_path, mode='a', allow_remove=False)

            # Create the destination group if it does not exist.
            try:
                rfile.create_group(dest_key)
            except RuntimeError as e:
                if 'A directory with name' in str(e):
                    print(f'{dest_key} already exists')
                    print('Will add samples to this group')
                else:
                    raise

            if cutoff is None:
                criteria = None
            else:
                criteria = Criteria(com_distance_sum, {}, cutoff=cutoff)

            sampler = Sampler(
                rfile, ref_key, rfile, dest_key, criteria=criteria,
                center_structures=center_structures
            )
            sampler.sample(sample_comp_ids, quantity)
    

    .. tab-item:: Dimer descriptor analysis

        .. image:: ./files/30h2o-md/30h2o.2h2o-com.sum-distribution-13457.png
            :width: 400px
            :align: center
    
    .. tab-item:: All monomer sampling

        .. code-block:: python

            import os
            from reptar import File, Sampler
            from reptar.descriptors import Criteria, com_distance_sum

            rfile_path = './30h2o-gfn2-md.exdir'

            group_key = '/30h2o'  # The parent group.
            ref_key = f'{group_key}/samples_3h2o'  # Group to sample from.
            dest_key = f'{group_key}/samples_1h2o'  # Where to store samples.


            sample_comp_ids = ['h2o']
            quantity = 'all'  # Number of trimers to sample.

            cutoff = None  # Value, list, or None. None accepts all structures.
            center_structures = True  # Translate center of mass to origin.
            structure_idxs = None  # None means all structures are options.

            # Ensures we execute from script directory (for relative paths).
            os.chdir(os.path.dirname(os.path.realpath(__file__)))

            rfile = File(rfile_path, mode='a', allow_remove=False)

            # Create the destination group if it does not exist.
            try:
                rfile.create_group(dest_key)
            except RuntimeError as e:
                if 'A directory with name' in str(e):
                    print(f'{dest_key} already exists')
                    print('Will add samples to this group')
                else:
                    raise

            criteria = Criteria(com_distance_sum, {}, cutoff=cutoff)

            sampler = Sampler(
                rfile, ref_key, rfile, dest_key,
                center_structures=center_structures
            )
            sampler.sample(sample_comp_ids, quantity)





Running Psi4 calculations
^^^^^^^^^^^^^^^^^^^^^^^^^

The following scripts show how to run DF-MP2/def2-TZVPPD calculations in Psi4 with reptar.
TODO: Finish this section.

.. caution::

    The following script uses a (at the time) development feature of Psi4: `freeze_core_policy <https://psicode.org/psi4manual/master/autodir_options_c/module__globals.html#freeze-core-policy>`__.
    Earlier versions of Psi4 would incorrectly freeze Li\ :sup:`+` orbitals, so we use ``freeze_core_policy`` to manually specify which orbitals to freeze.
    This feature should be released in v1.7, but if you are using an earlier version of Psi4 then just remove the relevant lines and be aware of this issue.

.. code-block:: text

    .
    └── 30h2o-sample-calculations
        ├── 30h2o-gfn2-md.exdir
        │   ├── samples_1h2o
        │   ├── samples_2h2o
        │   └── samples_3h2o
        ├── psi4-samples-1h2o
        │   ├── compute-psi4-engrads-1h2o.py
        │   └── submit-psi4.slurm
        ├── psi4-samples-2h2o
        │   ├── compute-psi4-engrads-2h2o.py
        │   └── submit-psi4.slurm
        ├── psi4-samples-3h2o
        │   ├── compute-psi4-engrads-3h2o.py
        │   └── submit-psi4.slurm

.. tab-set::

    .. tab-item:: compute-psi4-engrads-3h2o.py

        .. code-block:: python

            import sys
            import numpy as np
            import os
            from reptar import File, Saver
            from reptar.calculators.drivers import driverENGRAD
            from reptar.calculators.psi4_workers import psi4_engrad
            import time

            rfile_path = '../30h2o-gfn2-md.exdir'
            group_key = '/30h2o/samples_3h2o'
            E_key = f'{group_key}/energy_ele_df.mp2.def2tzvppd'
            G_key = f'{group_key}/grads_df.mp2.def2tzvppd'

            ray_address = str(sys.argv[2])

            use_ray = True
            n_cpus = int(sys.argv[1])
            n_cpus_worker = 4
            driver_kwargs = {
                'use_ray': use_ray, 'n_cpus': n_cpus, 'n_cpus_worker': n_cpus_worker,
                'chunk_size': 50, 'start_slice': None, 'end_slice': None, 'ray_address': ray_address
            }

            mem = 2*n_cpus_worker
            worker = psi4_engrad
            n_frozen_orbitals = [0]*4
            n_frozen_orbitals.extend([1]*8)
            n_frozen_orbitals.extend([5]*18)
            n_frozen_orbitals.extend([9]*8)
            # Setup Psi4 and system options.
            worker_kwargs = {
                'charge': 0, 'mult': 1, 'method': 'mp2', 'threads': n_cpus_worker,
                'mem': f'{mem} GB',
                'options': {
                    'reference': 'rhf',
                    'scf_type': 'df',
                    'mp2_type': 'df',
                    'e_convergence': 10,
                    'd_convergence': 10,
                    'basis': 'def2-tzvppd',
                    'df_basis_scf': 'def2-universal-jkfit',
                    'df_basis_mp2': 'def2-tzvppd-ri',
                    'freeze_core': 'policy',
                    'freeze_core_policy': n_frozen_orbitals,
                },
            }

            ###   SCRIPT   ###
            # Usually do not need to make any changes below this line.
            # Ensures we execute from script directory (for relative paths).
            os.chdir(os.path.dirname(os.path.realpath(__file__)))

            rfile = File(rfile_path, mode='a', allow_remove=False)

            Z = rfile.get(f'{group_key}/atomic_numbers')
            R = rfile.get(f'{group_key}/geometry')
            try:
                E = rfile.get(E_key)
            except RuntimeError as e:
                # Creates the property array if this is the initial job.
                if 'does not exist' in str(e):
                    E = np.empty((R.shape[0],))
                    E[:] = np.nan
                    rfile.put(E_key, E)
            try:
                G = rfile.get(G_key)
            except RuntimeError as e:
                # Creates the property array if this is the initial job.
                if 'does not exist' in str(e):
                    G = np.empty(R.shape)
                    G[:] = np.nan
                    rfile.put(G_key, G)

            # Saver object for energy and gradients after each work finishes.
            saver = Saver(rfile_path, (E_key, G_key))

            # Setup and run energy and gradient calculations.
            driver = driverENGRAD(
                Z, R, E, G, worker, worker_kwargs, **driver_kwargs
            )
            t_start = time.time()
            driver.run(saver=saver)
            t_end = time.time()

            print(f'Took {t_end-t_start:.1f} seconds')

    .. tab-item:: submit-psi4.slurm

        .. code-block:: bash

            #!/bin/bash
            #SBATCH --job-name=30h2o-samples_3h2o-df.mp2.def2tzvppd
            #SBATCH --output=30h2o-samples_3h2o-df.mp2.def2tzvppd.out
            #SBATCH --nodes=2
            #SBATCH --ntasks-per-node=48
            #SBATCH --time=1-00:00:00
            #SBATCH --cluster=mpi
            #SBATCH --partition=mpi
            #SBATCH --exclusive

            # Initialize conda environment
            module purge
            export PATH=~/miniconda3/condabin:$PATH
            source activate ~/miniconda3/envs/psi4-dev
            export PSI_SCRATCH=$SLURM_SCRATCH

            total_cpus=$(($SLURM_JOB_NUM_NODES * $SLURM_NTASKS_PER_NODE))

            ###   SETUP RAY   ###
            # Taken from https://docs.ray.io/en/master/cluster/vms/user-guides/community/slurm-basic.html#slurm-basic
            # __doc_head_address_start__

            # Getting the node names
            nodes=$(scontrol show hostnames "$SLURM_JOB_NODELIST")
            nodes_array=($nodes)

            head_node=${nodes_array[0]}
            head_node_ip=$(srun --nodes=1 --ntasks=1 -w "$head_node" hostname --ip-address)

            # if we detect a space character in the head node IP, we'll
            # convert it to an ipv4 address. This step is optional.
            if [[ "$head_node_ip" == *" "* ]]; then
            IFS=' ' read -ra ADDR <<<"$head_node_ip"
            if [[ ${#ADDR[0]} -gt 16 ]]; then
            head_node_ip=${ADDR[1]}
            else
            head_node_ip=${ADDR[0]}
            fi
            echo "IPV6 address detected. We split the IPV4 address as $head_node_ip"
            fi
            # __doc_head_address_end__

            # __doc_head_ray_start__
            port=6379
            ip_head=$head_node_ip:$port
            export ip_head
            echo "IP Head: $ip_head"

            echo "Starting HEAD at $head_node"
            srun --nodes=1 --ntasks=1 -w "$head_node" \
                ray start --head --node-ip-address="$head_node_ip" --port=$port \
                --num-cpus "${SLURM_NTASKS_PER_NODE}" --num-gpus "0" --block &
            # __doc_head_ray_end__

            # __doc_worker_ray_start__
            # optional, though may be useful in certain versions of Ray < 1.0.
            sleep 10

            # number of nodes other than the head node
            worker_num=$((SLURM_JOB_NUM_NODES - 1))

            for ((i = 1; i <= worker_num; i++)); do
                node_i=${nodes_array[$i]}
                echo "Starting WORKER $i at $node_i"
                srun --nodes=1 --ntasks=1 -w "$node_i" \
                    ray start --address "$ip_head" \
                    --num-cpus "${SLURM_NTASKS_PER_NODE}" --num-gpus "0" --block &
                sleep 5
            done
            # __doc_worker_ray_end__ 

            echo
            echo "Done setting up ray!"
            echo

            ###   RUN SCRIPT   ###
            cd ${SLURM_SUBMIT_DIR}
            python -u compute-psi4-engrads-3h2o.py $total_cpus $ip_head

