import re

from datetime import datetime

from jinja2 import Template
from wtforms import BooleanField, DecimalField, SelectField, StringField, Form, RadioField
from wtforms.validators import InputRequired
from wtforms.fields.html5 import IntegerField
from wtforms.widgets.html5 import NumberInput

class AdvancedOptionForm(Form):
    account = SelectField("Account")
    runtime = DecimalField('Time (hours)', validators=[InputRequired()], widget=NumberInput())
    ui      = SelectField('User interface')
    nprocs  = IntegerField('Number of cores', validators=[InputRequired()], widget=NumberInput())
    memory  = IntegerField('Memory (MB)',  validators=[InputRequired()], widget=NumberInput())
    gpus    = SelectField('GPU configuration')
    oversubscribe = BooleanField('Enable core oversubscription?')
    reservation = SelectField("Reservation")

    def __init__(self, template_path, form_params, prev_values):
        super().__init__()

        with open(template_path, 'r') as template_file:
            self.template = template_file.read()

        self.config_runtime(prev=prev_values.pop('runtime', None),
                            def_=form_params['runtime']['def_'],
                            min_=form_params['runtime']['min_'],
                            max_=form_params['runtime']['max_'],
                            step=form_params['runtime']['step'],
                            lock=form_params['runtime']['lock'])

        self.config_core(prev=prev_values.pop('nprocs', None),
                         def_=form_params['core']['def_'],
                         min_=form_params['core']['min_'],
                         max_=form_params['core']['max_'],
                         step=form_params['core']['step'],
                         lock=form_params['core']['lock'])

        self.config_memory(prev=prev_values.pop('memory', None),
                           def_=form_params['mem']['def_'],
                           min_=form_params['mem']['min_'],
                           max_=form_params['mem']['max_'],
                           step=form_params['mem']['step'],
                           lock=form_params['mem']['lock'])

        self.config_oversubscribe(prev=prev_values.pop('oversubscribe', None),
                                  def_=form_params['oversubscribe']['def_'],
                                  lock=form_params['oversubscribe']['lock'])

        self.config_gpus(prev=prev_values.pop('gpus', None),
                         def_=form_params['gpus']['def_'],
                         choices=form_params['gpus']['choices'],
                         lock=form_params['gpus']['lock'])

        self.config_ui(prev=prev_values.pop('ui', None),
                        def_=form_params['ui']['def_'],
                        choices=form_params['ui']['choices'],
                        lock=form_params['ui']['lock'])

        for field, value in prev_values.items():
            if value and field in self:
                self[field].data = value

    def render(self, accounts, reservations):
        self.set_account_choices(accounts)
        self.set_reservations(reservations)
        return Template(self.template).render(form=self)

    def config_runtime(self, prev, def_, min_, max_, step, lock):
        if prev is not None:
            # time is converted in minutes after submitting
            prev = round(prev / 60, 2)
            if min_ <= prev and (max_ is None or prev <= max_):
                self.runtime.data = prev
        else:
            self.runtime.data = def_
        self.runtime.widget.min = min_
        self.runtime.widget.max = max_
        self.runtime.widget.step = step
        if lock:
            self.runtime.render_kw = {'disabled': 'disabled'}
        self.runtime.filters = [lambda x: int(x * 60)]

    def config_core(self, prev, def_, min_, max_, step, lock):
        if prev is not None and min_ <= prev <= max_:
            self.nprocs.data = prev
        else:
            self.nprocs.data = def_
        self.nprocs.widget.min = min_
        self.nprocs.widget.max = max_
        self.nprocs.widget.step = step
        if lock:
            self.nprocs.render_kw = {'disabled': 'disabled'}

    def config_memory(self, prev, def_, min_, max_, step, lock):
        if prev is not None and min_ <= prev <= max_:
            self.memory.data = prev
        else:
            self.memory.data = def_
        self.memory.widget.min = min_
        self.memory.widget.max = max_
        self.memory.widget.step = step
        if lock:
            self.memory.render_kw = {'disabled': 'disabled'}

    def config_oversubscribe(self, prev, def_, lock):
        self.oversubscribe.data = def_
        if lock:
            self.oversubscribe.render_kw = {'disabled': 'disabled'}
        elif prev is not None:
            self.oversubscribe.data = prev

    def set_account_choices(self, accounts):
        self.account.choices = list(zip(accounts, accounts))

    def config_gpus(self, prev, def_, choices, lock):
        gpu_choices = {}
        if 'gpu:0' in choices:
            gpu_choices['gpu:0'] = 'None'
            choices.remove('gpu:0')
        for gres in choices:
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
        if prev is not None:
            self.gpus.data = prev
        else:
            self.gpus.data = def_
        if lock:
            self.gpus.render_kw = {'disabled': 'disabled'}

    def config_ui(self, prev, def_, choices, lock):
        self.ui.choices = choices
        if prev:
            self.ui.data = prev
        else:
            self.ui.data = def_
        if lock:
            self.ui.render_kw = {'disabled': 'disabled'}

    def set_reservations(self, reservation_list):
        now = datetime.now()
        choices = [("", "None")]
        for rsv in reservation_list:
            name = rsv['ReservationName']
            duration = rsv['EndTime'] - now
            string = '{} - time left: {}'.format(name, duration)
            choices.append((name, string))
        self.reservation.choices = choices
