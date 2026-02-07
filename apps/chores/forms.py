from django import forms
import json
from .models import Chore, Location, Equipment, Task

# Weekday choices for recurrence_day_of_week
WEEKDAY_CHOICES = [
    ('', '-----'),
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday'),
]


class ChoreForm(forms.ModelForm):
    # provide a select for weekday recurrence instead of free text
    recurrence_day_of_week = forms.ChoiceField(
        choices=WEEKDAY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'})
    )
    recurrence_day_of_month = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g. 5 or 5,15'})
    )
    class Meta:
        model = Chore
        fields = [
            'name',
            'description',
            'points',
            'penalize_incomplete',
            'penalty_amount',
            'is_recurring',
            'recurrence',
            'recurrence_day_of_week',
            'recurrence_day_of_month',
            'time_due',
            'instructions_video',
            'instructions_video_name',
            'instructions_video_source',
            'location',
            'equipment',
            'tasks',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'points': forms.NumberInput(attrs={'class': 'input input-bordered w-32'}),
            'penalty_amount': forms.NumberInput(attrs={'class': 'input input-bordered w-32'}),
            'penalize_incomplete': forms.CheckboxInput(attrs={'class': 'checkbox'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'checkbox'}),
            'recurrence': forms.Select(attrs={'class': 'select select-bordered'}),
            'recurrence_day_of_week': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'recurrence_day_of_month': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'time_due': forms.TimeInput(attrs={'class': 'input input-bordered w-40', 'type': 'time'}),
            'instructions_video': forms.ClearableFileInput(attrs={'class': 'file-input file-input-bordered w-full'}),
            'instructions_video_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'instructions_video_source': forms.URLInput(attrs={'class': 'input input-bordered w-full'}),
            'location': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'equipment': forms.SelectMultiple(attrs={'class': 'select select-bordered w-full'}),
            'tasks': forms.SelectMultiple(attrs={'class': 'select select-bordered w-full'}),
        }

    def clean(self):
        cleaned = super().clean()
        recurrence = cleaned.get('recurrence')

        # Normalize empty weekday to None
        wk = cleaned.get('recurrence_day_of_week')
        if wk in ['', None]:
            cleaned['recurrence_day_of_week'] = None

        # Normalize empty month-day to None
        md = cleaned.get('recurrence_day_of_month')
        if md in ['', None]:
            cleaned['recurrence_day_of_month'] = None

        # Enforce model-level expectations to avoid DB constraint errors
        if recurrence == 'M':
            # monthly: day_of_week must be null
            cleaned['recurrence_day_of_week'] = None
            # ensure day-of-month is present
            if not cleaned.get('recurrence_day_of_month'):
                raise forms.ValidationError('Monthly recurrence requires a day-of-month (eg. 5 or 5,15).')
            # validate day-of-month format (comma-separated ints 1-31)
            raw = cleaned.get('recurrence_day_of_month')
            parts = [p.strip() for p in str(raw).split(',') if p.strip()]
            days = []
            for p in parts:
                if not p.isdigit():
                    raise forms.ValidationError('Day-of-month must be integers (1-31), optionally comma-separated.')
                v = int(p)
                if v < 1 or v > 31:
                    raise forms.ValidationError('Day-of-month values must be between 1 and 31.')
                days.append(str(v))
            cleaned['recurrence_day_of_month'] = ','.join(days)

        if recurrence == 'W':
            # weekly: day_of_month must be null
            cleaned['recurrence_day_of_month'] = None
            # ensure a weekday is provided
            if not cleaned.get('recurrence_day_of_week'):
                raise forms.ValidationError('Weekly recurrence requires a weekday selection.')

        # If not recurring, clear recurrence fields
        if not cleaned.get('is_recurring'):
            cleaned['recurrence'] = None
            cleaned['recurrence_day_of_week'] = None
            cleaned['recurrence_day_of_month'] = None

        return cleaned


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        # include notes so templates can provide an array of strings
        fields = ['name', 'description', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            # notes will be filled by the client as JSON; keep it hidden in the form
            'notes': forms.HiddenInput(),
        }

    def clean_notes(self):
        """Normalize notes input into a list of strings for the JSONField.

        Accepts JSON array (preferred) or newline/comma separated text from the client UI.
        """
        raw = self.cleaned_data.get('notes')
        if raw in (None, '', []):
            return []
        # Treat literal JSON 'null' or string 'None' as empty
        if isinstance(raw, str) and raw.strip().lower() in ('null', 'none'):
            return []
        # If already a list (some clients may POST parsed data), pass through
        if isinstance(raw, list):
            return [str(x) for x in raw if x is not None and str(x).strip()]
        # Try to parse JSON
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed if x is not None and str(x).strip()]
        except Exception:
            # not JSON; fall back to splitting by newlines or commas
            pass
        # Split on newlines or commas
        parts = [p.strip() for p in str(raw).replace('\r', '').split('\n') if p.strip()]
        if len(parts) == 1 and ',' in parts[0]:
            parts = [p.strip() for p in parts[0].split(',') if p.strip()]
        return parts


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        # include notes so client-side UI can persist structured notes JSON
        fields = ['name', 'description', 'location', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'location': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            # notes will be populated by client UI as JSON; keep it hidden
            'notes': forms.HiddenInput(),
        }

    def clean_notes(self):
        """Normalize notes input into a list for the JSONField on Equipment.

        Accepts JSON array (preferred) or newline/comma separated text from the client UI.
        """
        raw = self.cleaned_data.get('notes')
        if raw in (None, '', []):
            return []
        if isinstance(raw, str) and raw.strip().lower() in ('null', 'none'):
            return []
        if isinstance(raw, list):
            return [str(x) for x in raw if x is not None and str(x).strip()]
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed if x is not None and str(x).strip()]
        except Exception:
            pass
        parts = [p.strip() for p in str(raw).replace('\r', '').split('\n') if p.strip()]
        if len(parts) == 1 and ',' in parts[0]:
            parts = [p.strip() for p in parts[0].split(',') if p.strip()]
        return parts


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        # include equipment and notes so the quick-add UI can set them
        fields = ['name', 'description', 'equipment', 'steps', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'equipment': forms.SelectMultiple(attrs={'class': 'select select-bordered w-full'}),
            # steps will be managed via client JS UI and stored as JSON in a hidden input
            'steps': forms.HiddenInput(),
            # notes will be populated by client UI as JSON; keep it hidden
            'notes': forms.HiddenInput(),
        }

    def clean_notes(self):
        """Normalize notes input into a list for the JSONField on Task.

        Accepts JSON array (preferred) or newline/comma separated text from the client UI.
        """
        raw = self.cleaned_data.get('notes')
        if raw in (None, '', []):
            return []
        if isinstance(raw, str) and raw.strip().lower() in ('null', 'none'):
            return []
        if isinstance(raw, list):
            return [str(x) for x in raw if x is not None and str(x).strip()]
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed if x is not None and str(x).strip()]
        except Exception:
            pass
        parts = [p.strip() for p in str(raw).replace('\r', '').split('\n') if p.strip()]
        if len(parts) == 1 and ',' in parts[0]:
            parts = [p.strip() for p in parts[0].split(',') if p.strip()]
        return parts

    def clean_steps(self):
        """Normalize steps input into a list of step dicts for the JSONField on Task.

        Expected format: JSON array of objects with at least `name` and optional `description` and `order`.
        We'll normalize to a list sorted by `order` (if present) or by appearance, and ensure `order` is integer indices.
        """
        raw = self.cleaned_data.get('steps')
        if raw in (None, '', []):
            return []
        if isinstance(raw, list):
            parsed = raw
        else:
            try:
                parsed = json.loads(raw)
            except Exception:
                # not JSON, treat as empty
                return []
        if not isinstance(parsed, list):
            return []
        # Map to dicts with name/description/order
        steps = []
        for i, item in enumerate(parsed):
            if not isinstance(item, dict):
                continue
            name = str(item.get('name') or '').strip()
            desc = item.get('description') or ''
            try:
                order = int(item.get('order')) if item.get('order') is not None else None
            except Exception:
                order = None
            if not name:
                # skip unnamed steps
                continue
            steps.append({'name': name, 'description': str(desc), 'order': order if order is not None else i})
        # sort by order then reindex
        steps.sort(key=lambda x: (x.get('order') if x.get('order') is not None else 0))
        for idx, s in enumerate(steps):
            s['order'] = idx
        return steps
