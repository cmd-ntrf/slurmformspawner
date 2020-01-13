# slurmformspawner
JupyterHub SlurmSpawner with a dynamic spawn form

## Configuration


| Variable                          | Type    | Description                                     | Default |
| --------------------------------- | :------ | :---------------------------------------------- | ------- |
| `c.SlurmFormSpawner.runtime_min`  | `Float` | Minimum runtime that can be requested in hours  | 0.25    |
| `c.SlurmFormSpawner.runtime_def`  | `Float` | Default runtime in the form in hours            | 1.0     |
| `c.SlurmFormSpawner.runtine_max`  | `Float` | Maximum runtime that can be requested in hours (0 means unlimited) | 12.0 |
| `c.SlurmFormSpawner.runtime_step` | `Float` | Runtime increment that can be requested in hours | 0.25 |
| `c.SlurmFormSpawner.runtime_lock` | `Bool`  | Disable user input for runtime | `False` |
| `c.SlurmFormSpawner.mem_min`      | `Integer` | Minimum amount of memory that can be requested in MB | 1024 |
| `c.SlurmFormSpawner.mem_def`      | `Integer` | Default amount of memory in the form in MB (0: maximum amounts of memory as configured in Slurm) | 0 |
| `c.SlurmFormSpawner.mem_max`      | `Integer` | Maximum amount of memory that can be requested in MB (0: maximum amounts of memory as configured in Slurm) | 0 |
| `c.SlurmFormSpawner.mem_step`     | `Integer` | Memory request range increment in MB | 1024 |
| `c.SlurmFormSpawner.mem_lock`     | `Bool`    | Disable user input for memory request | `False` |
| `c.SlurmFormSpawner.core_min`     | `Integer` | Minimum amount of cores | 1 |
| `c.SlurmFormSpawner.core_def`     | `Integer` | Default amount of cores (0: maximum number of cores as configured in Slurm) | 0 |
| `c.SlurmFormSpawner.core_max`     | `Integer` | Maximum amount of cores (0: maximum number of cores as configured in Slurm) | 0 |
| `c.SlurmFormSpawner.core_step`    | `Integer` | Core request range increment | 1 |
| `c.SlurmFormSpawner.core_lock`    | `Bool` | Disable user input for core request | 0 |
| `c.SlurmFormSpawner.oversubscribe_def`    | `Bool` | Default value for oversubscription | `False` |
| `c.SlurmFormSpawner.oversubscribe_lock`   | `Bool` | Disable user input for oversubscription | `False` |
| `c.SlurmFormSpawner.gpus_choices` | `Set` | Subset of options for gpu configuration. Example: `{'gpu:k20:1', 'gpu:k80:1'}`. An empty set keeps all options available in Slurm. | `Set()` |
| `c.SlurmFormSpawner.gpus_def`     | `Unicode` | Default value for gpu configuration. Example: `gpu:k20:1` | `''` |
| `c.SlurmFormSpawner.gpus_lock`    | `Bool` | Disable user input for gpu request | `False` |
| `c.SlurmFormSpawner.ui_def`       | `Unicode` | Default user interface. Choices: `['notebook', 'lab', 'terminal']` | `'notebook'` |
| `c.SlurmFormSpawner.ui_lock`      | `Bool` | Disable user input for user interface request | `False` |
| `c.SlurmFormSpawner.skip_form`    | `Bool` | Disable the spawner input form, use only default values instead | `False` |
| `c.SlurmFormSpawner.form_template_path` | `Unicode` | Path to the Jinja2 template of the form | `os.path.join(sys.prefix, 'share',  'slurmformspawner', 'templates', 'form.html')` |
| `c.SlurmFormSpawner.submit_template_path` | `Unicode` | Path to the Jinja2 template of the submit file | `os.path.join(sys.prefix, 'share', 'slurmformspawner', 'templates', 'submit.sh')` |

## screenshot

![form_screenshot](screenshot.png "Form screenshot")
