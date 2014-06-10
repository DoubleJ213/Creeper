"""
Threshold Form
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

RULES = {
    '1': {"max": 100, "min": 1}, # CPU
    '2': {"max": 100, "min": 1}, # Memory
    '4': {"max": 100, "min": 1}, # Network
    '5': {"max": 999999, "min": 1}, # IOWait
    '3': {"max": 100, "min": 1}, # Disk space
}

class ThresholdCreateForm(forms.Form):
    """
    Create form for create.html
    """
    threshold_name = forms.CharField(max_length=50, required=True)
    threshold_host = forms.CharField(required=True)
    threshold_type = forms.CharField(required=True)
    warning_value = forms.IntegerField(required=True)
    critical_value = forms.IntegerField(required=True)
    description = forms.CharField(max_length=255, required=True)

    def clean(self):
        data = super(forms.Form, self).clean()
        if data['warning_value'] >= data['critical_value']:
            raise ValidationError(
                _('Critical value must greater than warning value'))
        if data['threshold_type'] in RULES:
            t_max = RULES[data['threshold_type']]['max']
            t_min = RULES[data['threshold_type']]['min']
            if data['warning_value'] < t_min or data['warning_value'] > t_max:
                raise ValidationError(
                    _('Warning value must between %s and %s') % (t_min, t_max))
            elif data['critical_value'] < t_min or data[
                                                   'critical_value'] > t_max:
                raise ValidationError(
                    _('Critical value must between %s and %s') % (t_min, t_max))
        return data


class ThresholdUpdateForm(forms.Form):
    """
    Update form for update.html
    """
    threshold_type = forms.CharField(widget=forms.HiddenInput)
    threshold_name = forms.CharField(max_length=50, required=True)
    warning_value = forms.IntegerField(required=True)
    critical_value = forms.IntegerField(required=True)
    description = forms.CharField(max_length=255, required=True)

    def clean(self):
        data = super(forms.Form, self).clean()
        if data['warning_value'] >= data['critical_value']:
            raise ValidationError(
                _('Critical value must greater than warning value'))
        if data['threshold_type'] in RULES:
            max = RULES[data['threshold_type']]['max']
            min = RULES[data['threshold_type']]['min']
            if data['warning_value'] < min or data['warning_value'] > max:
                raise ValidationError(
                    _('Warning value must between %s and %s') % (min, max))
            elif data['critical_value'] < min or data['critical_value'] > max:
                raise ValidationError(
                    _('Critical value must between %s and %s') % (min, max))
        return data
