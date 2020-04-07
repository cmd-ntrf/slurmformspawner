# slurmformspawner
JupyterHub SlurmSpawner with a dynamic spawn form

## Requirements

- Python >= 3.6
- JupyterHub >= 1.0
- batchspawner>=0.9.0.dev0
- cachetools
- traitlets

## Configuration

### SlurmFormSpawner

| Variable                          | Type    | Description                                     | Default |
| --------------------------------- | :------ | :---------------------------------------------- | ------- |
| `c.SlurmFormSpawner.disable_form`    | `CBool` | Disable the spawner input form, use only default values instead | `False` |
| `c.SlurmFormSpawner.form_template_path` | `Unicode` | Path to the Jinja2 template of the form | `os.path.join(sys.prefix, 'share',  'slurmformspawner', 'templates', 'form.html')` |
| `c.SlurmFormSpawner.error_template_path` | `Unicode` | Path to the Jinja2 template of the error page | `os.path.join(sys.prefix, 'share',  'slurmformspawner', 'templates', 'error.html')` |
| `c.SlurmFormSpawner.submit_template_path` | `Unicode` | Path to the Jinja2 template of the submit file | `os.path.join(sys.prefix, 'share', 'slurmformspawner', 'templates', 'submit.sh')` |
| `c.SlurmFormSpawner.ui_args` | `Dict` | Dictionary of dictionaries describing the names and args of UI options | refer to `spawner.py` |

### SbatchForm

| Variable                          | Type    | Description                                     | Default |
| --------------------------------- | :------ | :---------------------------------------------- | ------- |
| `c.SbatchForm.runtime`  | `Dict({'max', 'min', 'step', 'lock', 'def'})` | Runtime widget parameters  | refer to `form.py`   |
| `c.SbatchForm.nprocs`  | `Dict({'max', 'min', 'step', 'lock', 'def'})` | Number of cores widget parameters | refer to `form.py` |
| `c.SbatchForm.memory`  | `Dict({'max', 'min', 'step', 'lock', 'def'})` | Memory (MB) widget parameters | refer to `form.py`    |
| `c.SbatchForm.oversubscribe`  | `Dict({'def', 'lock'})` | Oversubscribe widget parameters | refer to `form.py`  |
| `c.SbatchForm.gpus`  | `Dict({'def', 'choices', 'lock'})` | GPUs widget parameters | refer to `form.py`  |
| `c.SbatchForm.ui`  | `Dict({'def', 'choices', 'lock'})` | User interface widget parameters | refer to `form.py`  |
| `c.SbatchForm.reservation`  | `Dict({'def', 'choices', 'lock'})` | Reservation widget parameters | refer to `form.py`  |
| `c.SbatchForm.account`  | `Dict({'def', 'choices', 'lock'})` | Account widget parameters | refer to `form.py`  |

### SlurmAPI

| Variable                          | Type      | Description                                                       | Default |
| --------------------------------- | :-------- | :---------------------------------------------------------------- | ------- |
| `c.SlurmAPI.info_cache_ttl`       | `Integer` | Slurm sinfo output cache time-to-live (seconds)                   | 300     |
| `c.SlurmAPI.acct_cache_ttl`       | `Integer` | Slurm sacct output cache time-to-live (seconds)                   | 300     |
| `c.SlurmAPI.acct_cache_size`      | `Integer` | Slurm sacct output cache size (number of users)                   | 100     |
| `c.SlurmAPI.res_cache_ttl`        | `Integer` | Slurm scontrol (reservations) output cache time-to-live (seconds) | 300     |

## screenshot

![form_screenshot](screenshot.png "Form screenshot")
