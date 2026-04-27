# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Order(models.Model):
    order_id = models.UUIDField(primary_key=True)
    order_date = models.DateTimeField()
    payment_status = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    customer = models.ForeignKey('Customer', models.CASCADE)

    class Meta:
        managed = False
        db_table = 'ORDER'


class AccountRole(models.Model):
    pk = models.CompositePrimaryKey('role', 'user')
    role = models.ForeignKey('Role', models.CASCADE)
    user = models.ForeignKey('UserAccount', models.CASCADE)

    class Meta:
        managed = False
        db_table = 'account_role'


class Artist(models.Model):
    artist_id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100)
    genre = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'artist'


class Customer(models.Model):
    customer_id = models.UUIDField(primary_key=True)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    user = models.OneToOneField('UserAccount', models.CASCADE)

    class Meta:
        managed = False
        db_table = 'customer'


class Event(models.Model):
    event_id = models.UUIDField(primary_key=True)
    event_datetime = models.DateTimeField()
    event_title = models.CharField(max_length=200)
    venue = models.ForeignKey('Venue', models.CASCADE)
    organizer = models.ForeignKey('Organizer', models.CASCADE)

    class Meta:
        managed = False
        db_table = 'event'


class EventArtist(models.Model):
    pk = models.CompositePrimaryKey('event', 'artist')
    event = models.ForeignKey(Event, models.CASCADE)
    artist = models.ForeignKey(Artist, models.CASCADE)
    role = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'event_artist'


class HasRelationship(models.Model):
    pk = models.CompositePrimaryKey('seat', 'ticket')
    seat = models.ForeignKey('Seat', models.CASCADE)
    ticket = models.ForeignKey('Ticket', models.CASCADE)

    class Meta:
        managed = False
        db_table = 'has_relationship'


class OrderPromotion(models.Model):
    order_promotion_id = models.UUIDField(primary_key=True)
    promotion = models.ForeignKey('Promotion', models.CASCADE)
    order = models.ForeignKey(Order, models.CASCADE)

    class Meta:
        managed = False
        db_table = 'order_promotion'


class Organizer(models.Model):
    organizer_id = models.UUIDField(primary_key=True)
    organizer_name = models.CharField(max_length=100)
    contact_email = models.CharField(max_length=100)
    user = models.OneToOneField('UserAccount', models.CASCADE)

    class Meta:
        managed = False
        db_table = 'organizer'


class Promotion(models.Model):
    promotion_id = models.UUIDField(primary_key=True)
    promo_code = models.CharField(unique=True, max_length=50)
    discount_type = models.CharField(max_length=20)
    discount_value = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    usage_limit = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'promotion'


class Role(models.Model):
    role_id = models.UUIDField(primary_key=True)
    role_name = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'role'


class Seat(models.Model):
    seat_id = models.UUIDField(primary_key=True)
    section = models.CharField(max_length=50)
    seat_number = models.CharField(max_length=10)
    row_number = models.CharField(max_length=10)
    venue = models.ForeignKey('Venue', models.CASCADE)

    class Meta:
        managed = False
        db_table = 'seat'


class Ticket(models.Model):
    ticket_id = models.UUIDField(primary_key=True)
    ticket_code = models.CharField(unique=True, max_length=100)
    tcategory = models.ForeignKey('TicketCategory', models.CASCADE)
    torder = models.ForeignKey(Order, models.CASCADE)

    class Meta:
        managed = False
        db_table = 'ticket'


class TicketCategory(models.Model):
    category_id = models.UUIDField(primary_key=True)
    category_name = models.CharField(max_length=50)
    quota = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    tevent = models.ForeignKey(Event, models.CASCADE)

    class Meta:
        managed = False
        db_table = 'ticket_category'


class UserAccount(models.Model):
    user_id = models.UUIDField(primary_key=True)
    username = models.CharField(unique=True, max_length=100)
    password = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'user_account'


class Venue(models.Model):
    venue_id = models.UUIDField(primary_key=True)
    venue_name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    address = models.TextField()
    city = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'venue'
