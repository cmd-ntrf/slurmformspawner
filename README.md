# slurmformspawner
JupyterHub SlurmSpawner with a dynamic spawn form

## Configuration


| Variable                          | Type    | Description                                     | Default |
| --------------------------------- | :------ | :---------------------------------------------- | ------- |
| `c.SlurmFormSpawner.runtime_min`  | `Float` | Minimum runtime that can be requested in hours  | 0.25    |
| `c.SlurmFormSpawner.runtime_def`  | `Float` | Define the default runtime in the form in hours | 1.0     |
| `c.SlurmFormSpawner.runtine_max`  | `Float` | Maximum runtime that can be requested in hours (0 means unlimited) | 12.0 |
| `c.SlurmFormSpawner.runtime_step` | `Float` | Runtime increment that can be requested in hours | 0.25 |
| `c.SlurmFormSpawner.runtime_lock` | `Bool`  | Disable user input for runtime | `False` |
| `c.SlurmFormSpawner.mem_min`      | `Integer` | Minimum amount of memory that can be requested in MB | 1024 |
| `c.SlurmFormSpawner.mem_def`      | `Integer` | Define the default amount of memory in the form in MB (0: maximum amounts of memory as configured in Slurm) | 0 |
| `c.SlurmFormSpawner.mem_max`      | `Integer` | Maximum amount of memory that can be requested in MB (0: maximum amounts of memory as configured in Slurm) | 0 |
| `c.SlurmFormSpawner.mem_step`     | `Integer` | Define the step of size of memory request range in MB | 1024 |
| `c.SlurmFormSpawner.mem_lock`     | `Bool`    | Disable user input for memory request | `False` |
| `c.SlurmFormSpawner.core_min`     | `Integer` | Minimum amount of cores that can be requested | 1 |
| `c.SlurmFormSpawner.core_def`     | `Integer` | Define the default amount of cores in the form (0: maximum number of cores as configured in Slurm) | 0 |
| `c.SlurmFormSpawner.core_max`     | `Integer` | Maximum amount of cores that can be requested (0: maximum number of cores as configured in Slurm) | 0 |
| `c.SlurmFormSpawner.core_step`    | `Integer` | Define the step of cores request range | 1 |
| `c.SlurmFormSpawner.core_lock`    | `Bool` | Disable user input for core request | 0 |

## screenshot

![form_screenshot](screenshot.png "Form screenshot")
