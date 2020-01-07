import re

from datetime import datetime
from subprocess import check_output

from jinja2 import Template
from traitlets import Integer, Unicode, Float
from wtforms import BooleanField, DecimalField, SelectField, StringField, Form, RadioField
from wtforms.validators import InputRequired
from wtforms.fields.html5 import IntegerField
from wtforms.widgets.html5 import NumberInput

def get_slurm_cpus():
    cpus = check_output(['sinfo', '-h', '-e', '--format=%c'], encoding='utf-8').split()
    return list(map(int, cpus))

def get_slurm_accounts(username):
    output = check_output(['sacctmgr', 'show', 'user', username, 'withassoc',
                           'format=account', '-p', '--noheader'], encoding='utf-8').split()
    return [out.rstrip('|') for out in output]

def get_slurm_gres():
    return check_output(['sinfo', '-h', '--format=%G'], encoding='utf-8').split()

def get_slurm_active_reservations(username, accounts):
    accounts = set(accounts)
    reservations = check_output(['scontrol', 'show', 'res', '-o', '--quiet'], encoding='utf-8').strip().split('\n')
    if not reservations:
        return []
    reservations = [dict([item.split('=', maxsplit=1) for item in rsv.split()]) for rsv in reservations if rsv]
    for rsv in reservations:
        if rsv['State'] == 'ACTIVE':
            rsv['Users'] = set(rsv['Users'].split(','))
            rsv['Accounts'] = set(rsv['Accounts'].split(','))
            rsv['StartTime'] = datetime.strptime(rsv['StartTime'], "%Y-%m-%dT%H:%M:%S")
            rsv['EndTime'] = datetime.strptime(rsv['EndTime'], "%Y-%m-%dT%H:%M:%S")
            rsv['valid'] = username in rsv['Users'] or bool(accounts.intersection(rsv['Accounts']))
        else:
            rsv['valid'] = False
    return [rsv for rsv in reservations if rsv['valid']]

class SlurmSpawnerForm(Form):
    account = SelectField("Account")
    runtime = DecimalField('Time (hours)', validators=[InputRequired()],
                           widget=NumberInput(min=0.25, max=12, step=0.25))
    gui     = RadioField('GUI',
                         choices=[('notebook', 'Jupyter Notebook'), ('lab', 'JupyterLab')],
                         default='notebook')
    nprocs  = IntegerField('Number of cores', validators=[InputRequired()],
                           widget=NumberInput(min=1, step=1))
    memory  = IntegerField('Memory (MB)',  validators=[InputRequired()],
                           widget=NumberInput())
    gpus    = SelectField('GPU configuration')
    oversubscribe = BooleanField('Enable core oversubscription?')
    reservation = SelectField("Reservation")

    def __init__(self, username, template_path, form_params, prev_values):
        super().__init__()
        self.username = username
        self.set_nproc_max(get_slurm_cpus())
        self.set_gpu_choices(get_slurm_gres())

        with open(template_path, 'r') as template_file:
            self.template = template_file.read()

        self.memory.widget.min = form_params['mem_min']
        self.memory.widget.step = form_params['mem_step']
        self.memory.data = form_params['mem_def']
        if form_params['mem_lock']:
            self.memory.render_kw = {'disabled': 'disabled'}

        for field, value in prev_values.items():
            if value:
                self[field].data = value

        # Convert runtime to minutes
        if self['runtime'].data:
            self['runtime'].data = round(self['runtime'].data / 60, 2)
        self.runtime.filters = [lambda x: int(x * 60)]

    def render(self):
        accounts = get_slurm_accounts(self.username)
        reservations = get_slurm_active_reservations(self.username, accounts)
        self.set_account_choices(accounts)
        self.set_reservations(reservations)
        return Template(self.template).render(form=self)

    def set_nproc_max(self, cpu_choices):
        self.nprocs.widget.max = max(cpu_choices)

    def set_account_choices(self, accounts):
        self.account.choices = list(zip(accounts, accounts))

    def set_gpu_choices(self, gres_list):
        gpu_choices = {'gpu:0': 'None'}
        for gres in gres_list:
            match = re.match(r"(gpu:[\w:]+)", gres)
            if match:
                gres = match.group(1).split(':')
                number = int(gres[-1])
                if len(gres) == 2:
                    strings = ('gpu:{}', '{} x GPU')
                elif len(gres) > 2:
                    strings = ('gpu:{}:{{}}'.format(gres[1]), '{{}} x {}'.format(gres[1].upper()))
                for i in range(1, number + 1):
                    gpu_choices[strings[0].format(i)] = strings[1].format(i)
        self.gpus.choices = gpu_choices.items()

    def set_reservations(self, reservation_list):
        now = datetime.now()
        choices = [("", "None")]
        for rsv in reservation_list:
            name = rsv['ReservationName']
            duration = rsv['EndTime'] - now
            string = '{} - time left: {}'.format(name, duration)
            choices.append((name, string))
        self.reservation.choices = choices
