from django import forms
from web.models import Venue, Seat


class VenueSearchForm(forms.Form):
    """Form untuk search dan filter venue"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cari nama atau alamat...',
        })
    )
    
    city = forms.CharField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    seating_type = forms.CharField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get unique cities
        cities = Venue.objects.values_list('city', flat=True).distinct().order_by('city')
        city_choices = [('', 'Semua Kota')] + [(city, city) for city in cities]
        self.fields['city'].widget.choices = city_choices
        
        # Get unique seating types
        seating_types = Seat.objects.values_list('section', flat=True).distinct().order_by('section')
        seating_choices = [('', 'Semua Tipe Seating')] + [(st, st) for st in seating_types]
        self.fields['seating_type'].widget.choices = seating_choices


class CreateVenueForm(forms.ModelForm):
    """Form untuk membuat venue baru"""
    
    class Meta:
        model = Venue
        fields = ['venue_name', 'capacity', 'city', 'address']
        widgets = {
            'venue_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'cth. Jakarta Convention Center',
                'required': True,
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1000',
                'required': True,
                'min': '1',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Jakarta',
                'required': True,
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Jl. Gatot Subroto No.1',
                'rows': 4,
                'required': True,
            }),
        }
        labels = {
            'venue_name': 'NAMA VENUE (VENUE_NAME)',
            'capacity': 'KAPASITAS (CAPACITY)',
            'city': 'KOTA (CITY)',
            'address': 'ALAMAT (ADDRESS)',
        }
    
    has_reserved_seating = forms.BooleanField(
        required=False,
        label='Has Reserved Seating',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
