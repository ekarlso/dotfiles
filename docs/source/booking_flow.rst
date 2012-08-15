.. _installation:

Booking
=======

* What is a Booking ::
A Booking is allmost just like a association object of sorts, it's an object or
so meant to bind together information to provide information about when a
Entity is in use and things relating to it. Kind of like a "Order" in other
programs.


* Model information:
    * Price - Pricing information in some way
    * Start and End: Locations and Times respectively where Locations are
        relations to a Location
    * Customer - Who's the customer
    * Entities - What's booked

    * Any other convenience method or what is needed.


* Flows:
Search up entities which to book
(Free entities matching critera and that don't have booking within a given timeframe)

Booking.query.join(models.assoc_table, Booking.id==models.assoc_table.booking_id).all() agronholm ?/&w

